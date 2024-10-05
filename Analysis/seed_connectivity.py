import os
import pandas as pd
import numpy as np
import nilearn.image as image
import matplotlib.pyplot as plt
import nilearn.plotting as plotting
from nilearn.maskers import NiftiMasker
from nilearn.maskers import NiftiSpheresMasker


def process_subject(subj, run_id, run_dir, func_dir, func_name, regressor_name, reg_names, seed_img):
    try:
        print(f"Processing subject {subj}")
        func_file = os.path.join(func_dir, f'sub-{subj}', 'func', func_name.format(subj, run_id))
        confound_file = os.path.join(func_dir, f'sub-{subj}', 'func', regressor_name.format(subj, run_id))
        confound_factors = pd.read_csv(confound_file, sep="\t")
        confound_reg = confound_factors[reg_names].fillna(0.0)

        # 使用种子点方式提取时间序列
        # seed_masker = NiftiMasker(
        #     mask_img = seed_img,
        #     smoothing_fwhm=6,
        #     detrend=True,
        #     standardize="zscore_sample",
        #     standardize_confounds="zscore_sample",
        #     low_pass=None,
        #     high_pass=0.01,
        #     t_r=3,
        #     memory_level=0,
        #     verbose=1,
        # )

        seed_masker = NiftiSpheresMasker(
            seeds=seed_img,
            radius=5,
            detrend=True,
            standardize="zscore_sample",
            standardize_confounds="zscore_sample",
            low_pass=None,
            high_pass=0.01,
            t_r=3,
            memory_level=0,
            verbose=1,
        )

        seed_time_series = seed_masker.fit_transform(func_file, confounds=confound_reg)
        # print(seed_time_series.shape)
        seed_time_series = np.nanmean(seed_time_series, axis=1, keepdims=True)
        # print(seed_time_series.shape)

        mask_img = '/mnt/data/Template/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_desc-brain_mask.nii'
        brain_masker = NiftiMasker(
            mask_img = mask_img,
            smoothing_fwhm=6,
            detrend=True,
            standardize="zscore_sample",
            standardize_confounds="zscore_sample",
            low_pass=None,
            high_pass=0.01,
            t_r=3,
            memory_level=0,
            verbose=1,
        )

        brain_time_series = brain_masker.fit_transform(func_file, confounds=confound_reg)

        seed_to_voxel_correlations = (np.dot(brain_time_series.T, seed_time_series) / seed_time_series.shape[0])

        print(
            "Seed-to-voxel correlation shape: (%s, %s)"
            % seed_to_voxel_correlations.shape
        )

        seed_to_voxel_correlations_fisher_z = np.arctanh(seed_to_voxel_correlations)
        print(
            f"Seed-to-voxel correlation Fisher-z transformed: "
            f"min = {seed_to_voxel_correlations_fisher_z.min():.3f}; "
            f"max = {seed_to_voxel_correlations_fisher_z.max():.3f}"
        )
        seed_to_voxel_correlations_fisher_z_img = brain_masker.inverse_transform(
            seed_to_voxel_correlations_fisher_z.T
        )
        seed_to_voxel_correlations_fisher_z_img.to_filename(
            os.path.join(run_dir, f"sub-{subj}_LOFC_seed_correlation_z.nii.gz"))
        return (subj, run_id, "Success")
    except Exception as e:
        print(f"处理被试 {subj} 时出错: {str(e)}")


if __name__ == '__main__':
    # seed_imgs = image.load_img(r'/mnt/workdir/DCM/Docs/Mask/LOFC/LOFC_dk_mask.nii.gz')  # lLOFC 坐标
    seed_imgs = [(36, 30, -16), (-36, 30, -16)]

    # Loading the functional data
    func_dir = r'/mnt/workdir/Development_induction/Data/BIDS/derivatives/fmriprep'
    func_name = r'sub-{}_task-{}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    regressor_name = r'sub-{}_task-{}_desc-confounds_timeseries.tsv'

    reg_names = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z', 'csf', 'white_matter']

    participants_data = pd.read_excel("/mnt/workdir/Development_induction/Data/participants_TUS.xlsx")
    exp_sub_data = participants_data[participants_data['被试组别'] == '实验组']
    sub_ids = exp_sub_data['被试数据编号'].to_list()
    subjects = [p.split('-')[-1] for p in sub_ids]

    runs = {'prerest': 'pre-rest', 'postrest1': 'post-rest1', 'postrest2': 'post-rest2'}

    savedir = '/mnt/workdir/Development_induction/Data/BIDS/derivatives/connectivity/seed_voxel/erie_lofc'

    # 检查功能数据文件是否存在，并进一步过滤被试
    subjects_with_data = []
    for subj in subjects:
        all_runs_exist = True
        for run_id in runs:
            func_file = os.path.join(func_dir, f'sub-{subj}', 'func', func_name.format(subj, run_id))
            if not os.path.exists(func_file):
                print(f"被试 {subj} 的 run {run_id} 功能数据文件不存在")
                all_runs_exist = False
                break
        if all_runs_exist:
            subjects_with_data.append(subj)
        else:
            print(f"被试 {subj} 被过滤，因为缺少功能数据文件")

    print(f"检查功能数据文件后剩余 {len(subjects_with_data)} 名被试")

    # 更新被试列表
    subjects = subjects_with_data

    # 过滤 mean FD > 0.2 的被试
    filtered_subjects = []
    for subj in subjects:
        fd_files = []
        for run_id in runs:
            confound_file = os.path.join(func_dir, f'sub-{subj}', 'func', regressor_name.format(subj, run_id))
            fd_files.append(confound_file)

        mean_fds = []
        for fd_file in fd_files:
            confound_factors = pd.read_csv(fd_file, sep="\t")
            fd = confound_factors['framewise_displacement']
            mean_fd = np.nanmean(fd)
            mean_fds.append(mean_fd)

        overall_mean_fd = np.mean(mean_fds)
        if overall_mean_fd <= 0.2:
            filtered_subjects.append(subj)
        else:
            print(f"被试 {subj} 被过滤，平均 FD: {overall_mean_fd:.3f}")

    print(f"过滤后剩余 {len(filtered_subjects)} 名被试")

    # 使用过滤后的被试列表
    subjects = filtered_subjects
    for run_id in runs:
        run_dir = os.path.join(savedir, runs[run_id])
        os.makedirs(run_dir, exist_ok=True)

        # 使用循环处理每个被试
        for subj in subjects:
            result = process_subject(subj, run_id, run_dir, func_dir, func_name, regressor_name, reg_names, seed_imgs)
    print("处理完成。")