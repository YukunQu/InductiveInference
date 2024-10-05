# -*- coding: utf-8 -*-
"""
Spyder Editor
"""
import os
import time
import subprocess
import pandas as pd


participants_data = pd.read_excel("/mnt/workdir/Development_induction/Data/participants_TUS.xlsx")
exp_sub_data = participants_data[participants_data['被试组别'] == '控制组sham']
sub_ids = exp_sub_data['被试数据编号'].to_list()
sub_ids.remove('sub-009')
sub_ids.remove('sub-010')

fmriprep_dir = r'/mnt/workdir/Development_induction/Data/BIDS/derivatives/fmriprep'
exist_subjects = []
for file in os.listdir(fmriprep_dir):
    if 'sub-' in file:
        exist_subjects.append(file)

unexist_subjects = []
for f in sub_ids:
    if f not in exist_subjects:
        unexist_subjects.append(f)  # filter the subjects who are already exist

subject_list = [p.split('-')[-1] for p in unexist_subjects]
subject_list.sort()

# split the subjects into subject units. Each unit includes only five subjects to prevent memory overflow.
sub_list = []
sub_set_num = 0
sub_set = ''
for i,sub in enumerate(subject_list):
    sub_set = sub_set + sub + ' '
    sub_set_num = sub_set_num+1
    if sub_set_num == 9:
        sub_list.append(sub_set[:-1])
        sub_set_num = 0
        sub_set = ''
    elif i == (len(subject_list)-1):
        sub_list.append(sub_set[:-1])
    else:
        continue

#%%
command_surfer = 'fmriprep-docker {} {} participant --participant-label {} --fs-license-file {} --output-spaces MNI152NLin2009cAsym:res-2 MNI152NLin2009cAsym:res-native --no-tty -w {} --nthreads 30'

starttime = time.time()
for subj in sub_list:
    bids_dir = r'/mnt/workdir/Development_induction/Data/BIDS'
    out_dir = r'/mnt/workdir/Development_induction/Data/BIDS/derivatives/fmriprep'
    
    work_dir = r'/mnt/workdir/Development_induction/Data/workdir'
    freesurfer_license = r'/mnt/data/license.txt'
    command = command_surfer.format(bids_dir, out_dir, subj, freesurfer_license, work_dir)
    print("Command:",command)
    subprocess.call(command, shell=True)

endtime = time.time()
print('总共的时间为:', round((endtime - starttime)/60/60, 2), 'h')