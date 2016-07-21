import os
import subprocess
from csv import DictReader


def download_url(output_dir, url, spider=True):
    cmd = ['wget', '-P', output_dir, url]
    if spider:
        cmd.insert(1, '--spider')
    subprocess.check_call(cmd)


def run_downloads(storage_dir, csv_in, spider=True):
    with open(csv_in, 'r') as f:
        dr = DictReader(f)
        for row in dr:
            output_dir_name = '{}-{}'.format(row['Vector Processing Unit'], row['Name'].replace(' ', '').replace('-', ''))
            output_dir = os.path.join(storage_dir, output_dir_name)
            download_url(output_dir, row['Catchment URL'], spider=spider)


def unzip_catchment_files(directory):
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.7z'):
                os.chdir(dirpath)
                full = os.path.join(dirpath, f)
                # print dirpath
                # print full
                subprocess.check_call(['p7zip', '-d', full])


if __name__ == '__main__':
    csv_in = '/home/benkoziol/Dropbox/NESII/project/pmesh/office/Data Sources.csv'
    storage_dir = '/media/benkoziol/Extra Drive 1/data/pmesh/catchment_shapefiles'

    # run_downloads(storage_dir, csv_in, spider=False)
    unzip_catchment_files(storage_dir)
