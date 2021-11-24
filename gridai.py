#!/usr/bin/env python3

import fire
import subprocess
import shlex
import os
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import re
import logging
import time
import io
import json

class SearchParam:
  """search param"""
  obj_type:str
  col_name:str
  col_idx:str
  search_expr:str
  group_by:bool = False
  search_cond:str = None
  match_cnt:int = 0  
  match_idx:int = []  
  def __init__(self,obj_type:str, col_name:str, col_idx:str, search_expr: str, group_by:bool = False, search_cond:str = None, match_cnt:int=0, match_idx:List[int]=[]):
    self.obj_type = obj_type 
    self.col_name= col_name 
    self.col_idx= col_idx
    self.search_expr= search_expr
    self.group_by= group_by
    self.search_cond= search_cond
    self.match_cnt= match_cnt
    self.match_idx = match_idx
  def __str__(self):
    return(f"1={self.obj_type},2={self.col_name},3={self.col_idx},4={self.search_expr},5={self.group_by},6={self.search_cond},7={self.match_cnt},8={self.match_idx}")
  def __unicode__(self):
    return(u"{self.obj_type},{self.col_name},{self.col_idx},{self.search_expr},{self.group_by},{self.search_cond},{self.match_cnt},{self.match_idx}")

class GridRetry(object):
  """Rerun Grid.ai CLI waiting for success"""
  status_cols = {
    "run" : ["", "run", "project", "status", "duration", "experiments", "running", "queued", "completed", "failed", "stopped", ""],
    "session" : ["", "session", "status", "instance type", "duration", "url", ""],
    "datastores" : ["", "cluster id", "name", "version", "size", "created", "created by", "status", ""],
    "clusters" : ["", "id", "name", "type", "status", "created", ""],
    "history": ["", "run", "created at", "experiments", "failed", "stopped", "completed", ""],
  }

  exceed_time_cnt = 0
  cmd_errs_cnt = 0
  total_retry_cnt = 0
  search_params = []

  #the following is used for daisy chains
  po = None   # produced from cli
  csvs = []   # cli to csv
  kvs = []   # cli to k:v
  tally = {}  # csv to tally

  def __init__(self,
    cwd:str=os.getcwd(), log_level=logging.INFO, cmd_exec_timeout:int=120, max_term_cols:int=512, poll_interval_sec:int=60, 
    max_total_retry_cnt:int=60, max_comm_errs_cnt:int=2, max_cmd_errs_cnt:int=2, max_exceed_time_cnt:int=2,
    github_actions:bool=True,chain:bool = False, gha:bool = False,
    # used in status
    max_no_ids_cnt:int=3, max_no_match_cnt:int=0, max_some_match_cnt:int=3, max_state_flip_cnt:int=3,min_all_match_cnt:int=1,
    ):

    self.cwd = cwd 
    self.max_term_cols = max_term_cols 
    self.cmd_exec_timeout = cmd_exec_timeout 
    self.poll_interval_sec = poll_interval_sec 
    self.max_total_retry_cnt = max_total_retry_cnt
    self.max_exceed_time_cnt = max_exceed_time_cnt 
    self.max_comm_errs_cnt = max_comm_errs_cnt 
    self.max_cmd_errs_cnt = max_cmd_errs_cnt 
    self.github_actions = github_actions 
    self.log_level = log_level 
    self.chain = chain
    self.gha = gha

    if (min_all_match_cnt < 1): raise ValueError(f"min_all_match_cnt={min_all_match_cnt} must be greater than 0")
    self.max_no_ids_cnt = max_no_ids_cnt 
    self.max_no_match_cnt = max_no_match_cnt 
    self.max_some_match_cnt = max_some_match_cnt 
    self.min_all_match_cnt = min_all_match_cnt 
    self.max_state_flip_cnt = max_state_flip_cnt 

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', level=log_level)

  def __str__(self):
    if (len(self.kvs) == 0) and (len(self.csvs) == 0):
      return (self.po.stdout.decode("utf-8")+"\n"+self.po.stderr.decode("utf-8"))
    else:
      if self.gha:
        return "\n".join(f"::set-output name={kv[0].replace(' ', '_').lower()}::{kv[1]}" for kv in self.kvs)
      else:
        return json.dumps([self.kvs,self.csvs])

  def __grid_user(self):
    """convert teams grid user output to standard format"""
    try:
      if self.kvs[4][0] == 'Teams':
        team,role = self.kvs[5][0].split("-")
        team = team.strip()
        role = role.strip()
        if role == "Role":
          self.kvs[4][1] = team
          self.kvs[5][0] = role
    except:
      pass

  def status_to_kv(self, delimiter:str= ":"):
    """convert grid output to k:v format"""
    for l in self.po.stdout.decode("utf-8").splitlines():
      c = [x.strip() for x in re.split(delimiter, l)]
      current_field_count = len(c)
      if current_field_count > 1:
        self.kvs.append(c)
    self.__grid_user()  # clean grid user output for team        
    return self 

  def status_to_csv(self, head:int = None):
    """convert grid output to csv format"""
    csv = []
    n=0
    last_field_count = None
    for l in self.po.stdout.decode("utf-8").splitlines():
      c = [x.strip() for x in re.split('│|┃|\|', l)]
      current_field_count = len(c)
      if current_field_count > 1:
        if last_field_count is None:
          last_field_count = current_field_count
        elif current_field_count != last_field_count:
          last_field_count = current_field_count   
          logging.debug(f"new table found")
          self.csvs.append(csv)
          n=0
          csv = []
        csv.append(c)
        n += 1
        if head is not None and n >= head:
          break
    self.csvs.append(csv)
    return self

  def status_column_index(self, status_type:str, column_name:str) -> int:
    """Convert column name to index position"""
    return(self.status_cols[status_type.lower()].index(column_name.lower()) )

  def add_status_param(self, obj_type:str, obj_id_col:str, obj_id_exp:str, search_cond:str=None, group_by:bool=False):
    # make lowercase
    obj_type = obj_type.lower()
    obj_id_col = obj_id_col.lower()
    # convert to index postions
    obj_id_idx = self.status_column_index(obj_type,obj_id_col) 
    # convert to expr if not
    if isinstance(obj_id_exp, str): obj_id_exp = re.compile(obj_id_exp)
    # add to sequence
    sp = SearchParam(obj_type, obj_id_col, obj_id_idx, obj_id_exp, group_by=group_by, search_cond=search_cond)
    self.search_params.append(sp)
    logging.debug(sp)

  def set_status_param(self, obj_type:str, obj_id_col:str, obj_status_col:str, obj_id_exp:str, obj_status_exp:str):
    self.search_params=[]
    self.add_status_param(obj_type, obj_id_col, obj_id_exp)
    self.add_status_param(obj_type, obj_status_col, obj_status_exp, group_by=True)

    # for Fire to daisy chain command
    if (self.chain == True):
      return(self)

  def status_tally(self):
    """search grid status for id and status"""
    n=0
    match_cnt=0
    self.tally={}
    self.status_to_csv()
    for c in self.csvs[0]: # only use the first if there are multiples
      logging.debug(f"{c}" )
      n += 1
      found = True
      for s in self.search_params:
        # the tally should be ordered to the last column
        if s.group_by == True:
          logging.debug(f"self.tally {c[s.col_idx]}")
          try:
            self.tally[c[s.col_idx]] += 1
          except:  
            self.tally[c[s.col_idx]] = 1
        if s.search_expr.search(c[s.col_idx]):
          logging.info(f"matched {c[s.col_idx]}")
          s.match_cnt += 1
        else:
          found = False
          break
      if found == True:
        match_cnt += 1

    logging.info(f"{n} entries,{match_cnt} matches,{','.join(self.tally)}")
    
    return(n,match_cnt,",".join(self.tally),self.tally)    

  def cli(self, cmd:str):
    """run Grid.ai CLI command"""
    # shell is required to set the COLUMNS
    args = f"export COLUMNS={self.max_term_cols}; {cmd}"
    # po might not be defined on abend
    self.po = None
    while self.total_retry_cnt < self.max_total_retry_cnt:
      self.total_retry_cnt += 1
      try:
        self.po = subprocess.run(args, cwd=self.cwd, capture_output=True, shell=True, timeout=self.cmd_exec_timeout) 
        if self.po.returncode == 0:
          break
        else:
          self.cmd_errs_cnt += 1
          logging.info(f"{args}:total_retry_cnt {self.total_retry_cnt}/{self.max_total_retry_cnt}:cmd_errs_cnt {self.cmd_errs_cnt}/{self.max_cmd_errs_cnt} exited with {self.po.returncode}")
          logging.info(self.po.stderr.decode("utf-8"))
          logging.info(self.po.stdout.decode("utf-8")) 
          if self.cmd_errs_cnt >= self.max_cmd_errs_cnt: 
            break
      except subprocess.TimeoutExpired:
        self.exceed_time_cnt += 1
        logging.info(f"{args}:total_retry_cnt {self.total_retry_cnt}/{self.max_total_retry_cnt}:cmd_errs_cnt {self.exceed_time_cnt}/{self.max_exceed_time_cnt} exceeded timeout={self.cmd_exec_timeout}s")
        if self.exceed_time_cnt >= self.max_exceed_time_cnt: 
          break

      time.sleep(self.poll_interval_sec)
    return self
       
  def status_summary(self,cmd:str, obj_type:str, obj_id:str):
    # counters
    cmd_no_ids_cnt=0 
    cmd_no_match_cnt=0 
    cmd_some_match_cnt=0 
    cmd_all_match_cnt=0 
    cmd_state_flip_cnt=0
    # loop until the end
    rc=1
    while self.total_retry_cnt < self.max_total_retry_cnt:
      self.cli(cmd, cli_chain=True)
      # retried did not yield any results
      if self.po is None: 
        break

      total_entries, total_all_match, obj_summary, tally = self.status_tally()

      # exit condition checks
      if (self.search_params[0].match_cnt == 0):
        logging.info("id not found")
        cmd_no_ids_cnt += 1
        if (self.max_no_ids_cnt > 0 and cmd_no_ids_cnt >= self.max_no_ids_cnt ):
          break   
      elif ( self.search_params[1].match_cnt == 0 ):
        logging.info("none matched status")
        cmd_no_match_cnt += 1
        if ( self.max_no_match_cnt > 0 and cmd_no_match_cnt >= self.max_no_match_cnt ):
          break  
      elif (self.search_params[0].match_cnt != self.search_params[1].match_cnt ):
        logging.info("some matched status")
        cmd_some_match_cnt += 1
        if ( self.max_some_match_cnt > 0 and cmd_some_match_cnt >= self.max_some_match_cnt ):
          break
      elif (self.search_params[0].match_cnt == self.search_params[1].match_cnt ):
        logging.info(f"{cmd_all_match_cnt}:all matched status:")
        cmd_all_match_cnt += 1
        if ( cmd_all_match_cnt >= self.min_all_match_cnt ):
          rc=0        
          break
      else:  
        raise Exception("Should have never gotten here")

      # continue loop    
      self.total_retry_cnt += 1
      time.sleep(self.poll_interval_sec)

    # show the last output
    logging.info(self.po.stdout.decode("utf-8"))

    # return the last status code
    if (self.github_actions==True):
      print(f"::set-output name=obj-type::{obj_type}")
      print(f"::set-output name=obj-id::{obj_id}")
      print(f"::set-output name=obj-summary::{obj_summary}")
      print(f"::set-output name=obj-tally::{str(tally)}")
      print(f"::set-output name=obj-status::{','.join(tally.keys())}")
      print(f"::set-output name=obj-exit-code::{rc}")

    return(rc)

  def run(self, obj_id:str, obj_status_expr="succeeded|cancelled|failed|stopped", id_is_expr=False, obj_id_col:str="run" , obj_status_col:str="status"):
    obj_type="run"
    obj_id_expr=f"^{obj_id}-exp[0-9]+$" if id_is_expr==False else obj_id
    self.set_status_param(obj_type, obj_id_col, obj_status_col, obj_id_expr, obj_status_expr)
    self.status_summary(f"grid status {obj_id}", obj_type, obj_id )
  
  def session(self, obj_id:str, obj_status_expr:str="running|failed|stopped|paused", id_is_expr=False, obj_id_col:str="session", obj_status_col:str="status"):
    obj_type="session"
    obj_id_expr=f"^{obj_id}$"  if id_is_expr==False else obj_id
    self.set_status_param(obj_type, obj_id_col, obj_status_col, obj_id_expr, obj_status_expr)
    self.status_summary(f"grid session", obj_type, obj_id )

  def datastore(self, obj_id:str, obj_status_expr="Succeeded", id_is_expr=False, obj_id_col:str="name", obj_status_col:str="status"):
    obj_type="datastore"
    obj_id_expr=f"^{obj_id}$"  if id_is_expr==False else obj_id
    self.set_status_param(obj_type, obj_id_col, obj_status_col, obj_id_expr, obj_status_expr)
    self.status_summary(f"grid datastore", obj_type, obj_id )
    
  def clusters(self, obj_id:str, obj_status_expr="running|failed", id_is_expr=False, obj_id_col:str="id", obj_status_col:str="status"):
    obj_type="clusters"
    obj_id_expr=f"^{obj_id}$"  if id_is_expr==False else obj_id 
    self.set_status_param(obj_type, obj_id_col, obj_status_col, obj_id_expr, obj_status_expr)
    self.status_summary(f"grid clusters", obj_type, obj_id )

if __name__ == '__main__':
  fire.Fire(GridRetry)

