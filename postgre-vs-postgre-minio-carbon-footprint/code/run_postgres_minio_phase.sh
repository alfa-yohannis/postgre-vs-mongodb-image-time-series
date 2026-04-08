#!/bin/bash
set -e

bash ./run_postgre_minio_only.sh \
    360p_sd_image \
    480p_sd_image \
    720p_hd_image \
    1080p_fhd_image \
    1440p_qhd_image \
    4k_uhd_image \
    5k_uhd_image
