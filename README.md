# audio-transcription-api

Turn a list of audio or video URLs into transcripts and subtitles (TXT, SRT, WebVTT, JSON with timestamps)
with OpenAI's open source Whisper model, from one Python file.

- Standard library only, Python 3.8+. No `pip install`, no ffmpeg, no GPU on your machine.
- Works with direct file links: MP3, M4A, WAV, FLAC, OGG, OPUS, MP4, MOV, WebM, MKV.
- 99 languages, auto-detected per file, or `--translate` to get English text from any language.
- Long files are fine: the script starts a run and waits for it, so a 2-hour podcast does not hit a request timeout.

The transcription itself runs in the cloud on the [Media Transcriber Actor](https://apify.com/ctriolab/media-transcriber?utm_source=github&utm_medium=readme&utm_campaign=audio-transcription-api)
(faster-whisper on Apify). This repository is the client: it sends your URLs, waits, and writes the files.

## Quick start

1. Get an Apify API token: sign up at apify.com (the free plan includes monthly credit), then
   Console > Settings > API & Integrations.
2. Clone and set the token:

   ```bash
   git clone https://github.com/ctriolab/audio-transcription-api.git
   cd audio-transcription-api
   export APIFY_TOKEN=your_token          # Windows PowerShell: $env:APIFY_TOKEN="your_token"
   ```

3. Transcribe:

   ```bash
   python transcribe.py https://upload.wikimedia.org/wikipedia/commons/d/dd/Armstrong_Small_Step.ogg --formats srt,vtt
   ```

## Real output

The command above, run on 2026-11-18:

```text
Starting transcription of 1 file(s) with model base...
  run d7IF0fyQImaArHVLE is ready...
Armstrong_Small_Step: en, 24 s, 19 words -> txt, json, srt, vtt
Saved 1 transcript(s) to transcripts/
```

`transcripts/Armstrong_Small_Step.srt`:

```text
1
00:00:03,380 --> 00:00:15,180
and I'll step off the land now.

2
00:00:15,180 --> 00:00:18,180
It's one small step for man.

3
00:00:18,180 --> 00:00:23,810
One by a fleet for man.
```

The 1969 recording is noisy, and the `base` model misheard the last line. The same file with `--model small`:

```text
I'm going to step off the land now. That's one small step for man. One giant leap for mankind.
```

`transcripts/Armstrong_Small_Step.json` (segments shortened):

```json
{
  "url": "https://upload.wikimedia.org/wikipedia/commons/d/dd/Armstrong_Small_Step.ogg",
  "fileName": "Armstrong_Small_Step.ogg",
  "language": "en",
  "languageProbability": 0.894,
  "task": "transcribe",
  "model": "base",
  "durationSeconds": 24.11,
  "billedMinutes": 1,
  "text": "and I'll step off the land now. It's one small step for man. One by a fleet for man.",
  "wordCount": 19,
  "segmentCount": 3,
  "segments": [{ "start": 3.38, "end": 15.18, "text": "and I'll step off the land now." }],
  "srtUrl": "https://api.apify.com/v2/key-value-stores/<store id>/records/001-Armstrong_Small_Step.srt",
  "vttUrl": "https://api.apify.com/v2/key-value-stores/<store id>/records/001-Armstrong_Small_Step.vtt",
  "processingSeconds": 2,
  "transcribedAt": "2026-11-18T11:33:49+00:00"
}
```

## More examples

```bash
# Many files: one URL per line in urls.txt (lines starting with # are skipped)
python transcribe.py --list urls.txt --out podcast

# German interview, most accurate model, subtitles in all three formats
python transcribe.py https://example.com/interview.mp4 --language de --model small --formats srt,vtt,txt

# Any language to English text, no subtitle files
python transcribe.py https://example.com/talk.mp3 --translate --formats none
```

| Option | Default | Meaning |
|---|---|---|
| `--model` | `base` | `tiny` (fastest), `base`, `small` (most accurate, about 3x slower than base) |
| `--language` | auto | ISO 639-1 code: `en`, `de`, `es`, `ko`, `ja`... |
| `--translate` | off | English text for speech in any language |
| `--formats` | `srt,vtt` | Subtitle files to save: any of `srt`, `vtt`, `txt`, or `none` |
| `--no-segments` | off | Leave timestamped segments out of the `.json` |
| `--list` | | Text file with one URL per line |
| `--out` | `transcripts` | Output folder. Per file: `<name>.txt`, `<name>.json`, and the subtitle files |

Files that are not media, longer than 4 hours, or silent are skipped (and not charged); the script prints how many.

## Limits of this script

- Links must return the file itself. YouTube, TikTok and Instagram pages are not supported.
- No speaker labels (diarization).
- Local files: upload them somewhere that gives a direct link first (for example an Apify key-value store,
  which the Actor can read directly from its input).

## Hosted version on Apify

The transcription runs on **[Media Transcriber on Apify](https://apify.com/ctriolab/media-transcriber?utm_source=github&utm_medium=readme&utm_campaign=audio-transcription-api)**.
It is billed to your own Apify account per audio minute ($1.50 per 1,000 minutes on the free plan, less on paid plans) plus Apify platform usage;
the 24-second example above used under $0.01 of platform usage. From the Apify Console you can also schedule it,
use "only new files" for a podcast feed, and send results to Google Sheets, Make, Zapier or a webhook.

If this Actor saved you time, a short review on its Apify Store page helps other people find it. Thank you.

This example is maintained by Ctrio Lab, the maker of the Actor.

## License

MIT. See [LICENSE](LICENSE).
