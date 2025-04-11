#!/usr/bin/env python3

import argparse
import csv
import os
import os.path
import subprocess

os.makedirs('images', exist_ok=True)
os.makedirs('normalized', exist_ok=True)
os.makedirs('output', exist_ok=True)

def run(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        print(cmd)
        print(proc.stderr.decode('utf-8'))

def norm_audio(fname, video=False):
    cmd = ['ffmpeg-normalize', '-f', fname]
    if not video:
        cmd.append('-e="-vn"')
    run(cmd)
    return 'normalized/' + os.path.splitext(fname)[0] + '.mkv'

def pptx2png(fname, number):
    run(['soffice', '--headless', '--convert-to', 'pdf',
         fname, '--outdir', 'images'])
    base = os.path.splitext(fname)[0]
    run(['gs', '-sDEVICE=pngalpha', '-r144', '-o',
         f'images/{base}%d.png', f'images/{base}.pdf'])
    if '|' in number:
        return [f'images/{base}{i}.png'
                for i in range(1, number.count('|')+2)]
    return f'images/{base}{number}.png'

def combine(slide, audio, out):
    run(['ffmpeg', '-y', '-i', slide, '-i', audio, '-vf', 'scale=1920:-1', out])

def combine_multi(slides, times, audio, prefix):
    ret = []
    for i, (slide, start) in enumerate(zip(slides, times)):
        cmd = ['ffmpeg', '-y', '-i', slide, '-ss', start]
        if i + 1 < len(times):
            cmd += ['-to', times[i+1]]
        vid = f'{prefix}_{i}.mp4'
        cmd += ['-i', audio, '-vf', 'scale=1920:-1', vid]
        ret.append(vid)
        run(cmd)
    return ret

def resize_video(vin, vout):
    run(['ffmpeg', '-y', '-i', vin, '-vf', 'scale=1920:-1', vout])

parser = argparse.ArgumentParser()
parser.add_argument('sheet', action='store')
parser.add_argument('prefix', action='store')
args = parser.parse_args()

videos = []
current_time = 0
chapters = []
def add_video(fname):
    global videos, current_time
    if isinstance(fname, list):
        for f in fname:
            add_video(f)
    else:
        proc = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', fname],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        current_time += float(proc.stdout)
        print('Produced clip', fname)
        videos.append(fname)

with open(args.sheet, newline='') as fin:
    reader = csv.DictReader(fin)
    for row in reader:
        step = row['Step']
        if row.get('Chapter'):
            t_s = round(current_time)
            t_m, t_s = divmod(t_s, 60)
            t_h, t_m = divmod(t_m, 60)
            chapters.append(f'[{t_h:02}:{t_m:02}:{t_s:02}] {row["Chapter"]}')
        if row['Video']:
            vin = norm_audio(row['Video'], video=True)
            vout = f'output/{args.prefix}_{step}.mp4'
            resize_video(vin, vout)
            add_video(vout)
            continue
        if not row['Slide'] or not row['Audio']:
            print('Missing step', step, 'from', row['Person'],
                  'in', args.prefix)
            continue
        num = row.get('Slide Number') or '1'
        slide = pptx2png(row['Slide'], num)
        print('Converted', row['Slide'], 'to', slide)
        audio = norm_audio(row['Audio'])
        print('Converted', row['Audio'], 'to', audio)
        if isinstance(slide, list):
            vls = combine_multi(slide, num.split('|'), audio,
                                f'output/{args.prefix}_{step}')
            add_video(vls)
        else:
            video = f'output/{args.prefix}_{step}.mp4'
            combine(slide, audio, video)
            add_video(video)

cmd = ['ffmpeg', '-y']
fc = []
for i, v in enumerate(videos):
    cmd += ['-i', v]
    fc += [f'[{i}:v]', f'[{i}:a]']
cmd += ['-filter_complex',
        ' '.join(fc) + f' concat=n={len(videos)}:v=1:a=1 [v] [a]',
        '-map', '[v]', '-map', '[a]', f'output/{args.prefix}.mp4']
run(cmd)

with open(f'output/{args.prefix}_chapters.txt', 'w') as fout:
    fout.write('\n'.join(chapters) + '\n')
