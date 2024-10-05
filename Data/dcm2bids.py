#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  9 21:02:34 2022

@author: dell
"""
import os
import subprocess

def dcm2bids_helper():
    # generate the help files for dicom to bids
    import subprocess
    d = r'/mnt/workdir/Development_induction/Data/Sourcedata/sub-020/NeuroData/MRI'
    o = r'/mnt/workdir/Development_induction/Data/Sourcedata/sub-020/NeuroData'
    command = r'dcm2bids_helper -d {} -o {}'.format(d, o)
    print("Command:", command)
    subprocess.call(command, shell=True)
dcm2bids_helper()

# %%
import os
import subprocess
import pandas as pd
from pypinyin import pinyin, Style


def chinese_to_pinyin_uppercase(chinese_name):
    pinyin_list = pinyin(chinese_name, style=Style.NORMAL)
    return ''.join([item[0].upper() for item in pinyin_list])


def dcm2bids(sub_ids, sub_names):
    for sub_id, subj in zip(sub_ids, sub_names):
        sub_dir = f'/mnt/workdir/Development_induction/Data/Sourcedata/{sub_id}/NeuroData/MRI'
        all_items = os.listdir(sub_dir)

        # 筛选出文件夹
        folders = [item for item in all_items if os.path.isdir(os.path.join(sub_dir, item))]

        sub_dcm_dirnames = []
        uppercase_pinyin = chinese_to_pinyin_uppercase(subj)

        sub_dcm_dirnames.append(uppercase_pinyin)
        sub_dcm_dirnames.append(f"{uppercase_pinyin}_A")
        sub_dcm_dirnames.append(f"{uppercase_pinyin}_B")
        sub_dcm_dirnames.append(f"{uppercase_pinyin}_C")

        for f in folders:
            postfix = f.split('_')[-1]
            print("Postfix:", postfix)
            if postfix == uppercase_pinyin:
                config = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/config/config_t1w.json'
            elif postfix == 'A':
                config = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/config/config_prerest.json'
            elif postfix == 'B':
                config = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/config/config_postrest1.json'
            elif postfix == 'C':
                config = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/config/config_postrest2.json'
            else:
                raise Warning(f"The folder {f} is not expected. Pinyin is {uppercase_pinyin} ")

            ori_dir = os.path.join(sub_dir, f)
            out_dir = r'/mnt/workdir/Development_induction/Data/BIDS'
            command = r'dcm2bids -d {} -p {} -c {} -o {} --forceDcm2niix'.format(ori_dir, sub_id, config, out_dir)
            print("Command:", command)
            subprocess.call(command, shell=True)


participants_data = pd.read_excel("/mnt/workdir/Development_induction/Data/participants_TUS.xlsx")
exp_sub_data = participants_data[participants_data['被试组别'] == '控制组sham']
sub_ids = exp_sub_data['被试数据编号'].to_list()
sub_names = exp_sub_data['被试姓名'].to_list()
dcm2bids(sub_ids, sub_names)