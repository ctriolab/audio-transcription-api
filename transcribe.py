#!/usr/bin/env python3
"""Transcribe audio and video URLs with Whisper through the Apify API.

Standard library only (Python 3.8+). Set APIFY_TOKEN, pass file URLs, and get
one folder with a .txt transcript, a .json result and optional .srt/.vtt
subtitles per file.

    python transcribe.py https://example.com/episode.mp3 --formats srt,vtt
    python transcribe.py --list urls.txt --model small --out transcripts
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = 'https://api.apify.com/v2'
ACTOR = 'ctriolab~media-transcriber'


def api_request(method, url, token, body=None, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    })
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()
                return payload if raw else json.loads(payload)
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            detail = error.read().decode(errors='replace')[:300]
            sys.exit(f'Apify API {method} {url.split("?")[0]} failed: HTTP {error.code} {detail}')
        except urllib.error.URLError as error:
            if attempt < 4:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f'Network error: {error.reason}')


def start_run(token, actor_input, memory_mb):
    query = urllib.parse.urlencode({'memory': memory_mb} if memory_mb else {})
    url = f'{API}/acts/{ACTOR}/runs' + (f'?{query}' if query else '')
    return api_request('POST', url, token, actor_input)['data']


def wait_for_run(token, run):
    # Long podcasts take longer than the 300 s limit of run-sync, so start the
    # run and poll it instead.
    while run['status'] in ('READY', 'RUNNING'):
        print(f'  run {run["id"]} is {run["status"].lower()}...', file=sys.stderr)
        run = api_request('GET', f'{API}/actor-runs/{run["id"]}?waitForFinish=60', token)['data']
    return run


def safe_name(name, used):
    stem = re.sub(r'[^A-Za-z0-9._-]+', '_', Path(name or 'file').stem).strip('._') or 'file'
    candidate, number = stem, 2
    while candidate in used:
        candidate, number = f'{stem}_{number}', number + 1
    used.add(candidate)
    return candidate


def read_urls(args):
    urls = list(args.urls)
    if args.list:
        for line in Path(args.list).read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(description='Transcribe audio/video URLs with Whisper on Apify.')
    parser.add_argument('urls', nargs='*', help='direct links to MP3, M4A, WAV, OGG, MP4, MOV, WebM... files')
    parser.add_argument('--list', help='text file with one URL per line')
    parser.add_argument('--out', default='transcripts', help='output folder (default: transcripts)')
    parser.add_argument('--model', choices=['tiny', 'base', 'small'], default='base')
    parser.add_argument('--language', help='ISO 639-1 code such as en, de, ko. Default: auto-detect')
    parser.add_argument('--translate', action='store_true', help='return English text for any language')
    parser.add_argument('--formats', default='srt,vtt', help='subtitle files to save: any of srt,vtt,txt, or "none"')
    parser.add_argument('--no-segments', action='store_true', help='do not include timestamped segments in the .json')
    parser.add_argument('--memory', type=int, help='run memory in MB (default: the Actor default)')
    args = parser.parse_args()

    token = os.environ.get('APIFY_TOKEN')
    if not token:
        sys.exit('Set APIFY_TOKEN first (Apify Console > Settings > API & Integrations).')
    urls = read_urls(args)
    if not urls:
        parser.error('give at least one URL or --list')
    formats = [] if args.formats == 'none' else [f.strip() for f in args.formats.split(',') if f.strip()]

    actor_input = {
        'mediaUrls': urls,
        'model': args.model,
        'task': 'translate' if args.translate else 'transcribe',
        'subtitleFormats': formats,
        'includeSegments': not args.no_segments,
    }
    if args.language:
        actor_input['language'] = args.language

    print(f'Starting transcription of {len(urls)} file(s) with model {args.model}...', file=sys.stderr)
    run = wait_for_run(token, start_run(token, actor_input, args.memory))
    if run['status'] != 'SUCCEEDED':
        sys.exit(f'Run {run["id"]} ended with status {run["status"]}: {run.get("statusMessage")}')

    items = api_request('GET', f'{API}/datasets/{run["defaultDatasetId"]}/items?clean=true&format=json', token)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    used = set()
    for item in items:
        stem = safe_name(item.get('fileName'), used)
        (out / f'{stem}.txt').write_text(item['text'] + '\n', encoding='utf-8')
        (out / f'{stem}.json').write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')
        saved = ['txt', 'json']
        for fmt in ('srt', 'vtt'):
            link = item.get(f'{fmt}Url')
            if link:
                (out / f'{stem}.{fmt}').write_bytes(api_request('GET', link, token, raw=True))
                saved.append(fmt)
        print(f'{stem}: {item["language"]}, {item["durationSeconds"]:.0f} s, '
              f'{item["wordCount"]} words -> {", ".join(saved)}')

    skipped = len(urls) - len(items)
    if skipped:
        print(f'{skipped} file(s) were skipped (not a media file, too long, no speech). '
              f'See the run log: https://console.apify.com/view/runs/{run["id"]}', file=sys.stderr)
    print(f'Saved {len(items)} transcript(s) to {out}/', file=sys.stderr)


if __name__ == '__main__':
    main()
