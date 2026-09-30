#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(git rev-parse --show-toplevel)"
OUT="submission/render"
mkdir -p "$OUT"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RAW="submission/wexspace-runtime.mp4"
ARCH="architecture/architecture_submission.png"
VOICE_URL="https://www.aidocmaker.com/g0/audio?name=8603c14036494ea6ad14be274df717fe"
test -s "$RAW"
test -s "$ARCH"

card () {
  local dur="$1" title="$2" sub="$3" out="$4"
  local fadeout
  fadeout="$(python3 - <<PY
print(max(0,float("$dur")-0.35))
PY
)"
  ffmpeg -hide_banner -loglevel error -y     -f lavfi -i "color=c=0x071612:s=1920x1080:r=30:d=$dur"     -vf "drawbox=x=0:y=0:w=iw:h=ih:color=0x0c2b22@0.45:t=fill,drawbox=x='mod(t*180,2200)-500':y=130:w=760:h=8:color=0x7bf5c2@0.75:t=fill,drawtext=fontfile=$BOLD:text='$title':fontcolor=white:fontsize=76:x=(w-text_w)/2:y=360:alpha='if(lt(t,0.6),t/0.6,if(gt(t,$dur-0.7),($dur-t)/0.7,1))',drawtext=fontfile=$FONT:text='$sub':fontcolor=0xB4DCCC:fontsize=34:x=(w-text_w)/2:y=490,fade=t=in:st=0:d=0.35,fade=t=out:st=$fadeout:d=0.35,format=yuv420p"     -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$out"
}

runtime_scene () {
  local dur="$1" seek="$2" title="$3" sub="$4" out="$5"
  local fadeout
  fadeout="$(python3 - <<PY
print(max(0,float("$dur")-0.25))
PY
)"
  ffmpeg -hide_banner -loglevel error -y     -stream_loop -1 -ss "$seek" -i "$RAW" -t "$dur"     -filter_complex "[0:v]split=2[bg][fg];[bg]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=25:12,eq=brightness=-0.18:saturation=0.75[bg2];[fg]scale=-2:940[fg2];[bg2][fg2]overlay=(W-w)/2:(H-h)/2,drawbox=x=70:y=55:w=1780:h=118:color=0x071612@0.80:t=fill,drawtext=fontfile=$BOLD:text='$title':fontcolor=0x7BF5C2:fontsize=48:x=110:y=78,drawtext=fontfile=$FONT:text='$sub':fontcolor=white:fontsize=28:x=110:y=137,fade=t=in:st=0:d=0.25,fade=t=out:st=$fadeout:d=0.25,format=yuv420p[v]"     -map "[v]" -an -r 30 -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$out"
}

card 7 "WEXSPACE AI" "Multiple projects. One durable execution model." "$OUT/01-intro.mp4"
runtime_scene 15 0 "ENGINEERING PROJECT" "Deterministic request -> result -> evidence" "$OUT/02-engineering.mp4"
runtime_scene 14 11 "SOFTWARE / QA PROJECT" "Governed tasks, checks and persistent results" "$OUT/03-software.mp4"

ffmpeg -hide_banner -loglevel error -y -loop 1 -i "$ARCH" -t 13   -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:0x071612,zoompan=z='min(zoom+0.0007,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=390:s=1920x1080:fps=30,drawbox=x=70:y=55:w=1780:h=118:color=0x071612@0.82:t=fill,drawtext=fontfile=$BOLD:text='WEXSPACE STUDIO OS':fontcolor=0x7BF5C2:fontsize=48:x=110:y=78,drawtext=fontfile=$FONT:text='Production Job #001 -> capture -> evidence -> QA':fontcolor=white:fontsize=28:x=110:y=137,fade=t=in:st=0:d=0.3,fade=t=out:st=12.7:d=0.3,format=yuv420p"   -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$OUT/04-studio.mp4"

runtime_scene 12 5 "CONTINUITY" "Preserved state. Completed work stays completed." "$OUT/05-continuity.mp4"
card 21 "REVENUECAT -> WEXSPACE PRO" "SDK 10.15.1 integrated. Live purchase qualification remains explicit." "$OUT/06-revenuecat.mp4"

ffmpeg -hide_banner -loglevel error -y -loop 1 -i "$ARCH" -t 14   -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:0x071612,zoompan=z='min(zoom+0.0005,1.07)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=420:s=1920x1080:fps=30,drawbox=x=105:y=740:w=1710:h=245:color=0x071612@0.86:t=fill,drawtext=fontfile=$BOLD:text='HUMAN-GOVERNED EXECUTION':fontcolor=0x7BF5C2:fontsize=48:x=145:y=780,drawtext=fontfile=$FONT:text='Configured != Authorized != Executed != Verified':fontcolor=white:fontsize=34:x=145:y=852,drawtext=fontfile=$FONT:text='Evidence and authority remain separate product states.':fontcolor=0xB4DCCC:fontsize=28:x=145:y=915,fade=t=in:st=0:d=0.3,fade=t=out:st=13.7:d=0.3,format=yuv420p"   -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$OUT/07-governance.mp4"

card 10 "NEXT GEN / PUBLIC SOURCE" "Android source + reproducible evidence in the public repository" "$OUT/08-open.mp4"
card 9 "WEXSPACE AI" "One workspace. Multiple specialist projects. Durable execution with proof." "$OUT/09-close.mp4"

cat > "$OUT/concat.txt" <<'EOF'
file '01-intro.mp4'
file '02-engineering.mp4'
file '03-software.mp4'
file '04-studio.mp4'
file '05-continuity.mp4'
file '06-revenuecat.mp4'
file '07-governance.mp4'
file '08-open.mp4'
file '09-close.mp4'
EOF
(cd "$OUT" && ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i concat.txt -c copy video-silent.mp4)

cat > "$OUT/captions.srt" <<'EOF'
1
00:00:00,000 --> 00:00:07,000
WEXSPACE AI — human-governed execution across specialist domains.

2
00:00:07,000 --> 00:00:22,000
Engineering: deterministic work with a reproducible result and evidence.

3
00:00:22,000 --> 00:00:36,000
Software / QA: governed checks, tasks and results stay tied to the work.

4
00:00:36,000 --> 00:00:49,000
Studio OS applies the same model to scenes, capture, evidence and QA.

5
00:00:49,000 --> 00:01:01,000
Projects share a continuity model: completed work stays completed.

6
00:01:01,000 --> 00:01:22,000
RevenueCat SDK 10.15.1 is integrated as the WEXSPACE Pro entitlement layer.
The live purchase path is never simulated.

7
00:01:22,000 --> 00:01:36,000
Configured, authorized, executed and verified are separate product states.

8
00:01:36,000 --> 00:01:46,000
Next Gen source is publicly reviewable and evidence-backed.

9
00:01:46,000 --> 00:01:55,000
One workspace. Multiple specialist projects. Durable execution with proof.
EOF

if curl -fL --retry 2 --connect-timeout 15 "$VOICE_URL" -o "$OUT/voice.mp3"; then
  ffmpeg -hide_banner -loglevel error -y     -i "$OUT/video-silent.mp4" -i "$OUT/voice.mp3"     -filter_complex "[0:v]subtitles='$OUT/captions.srt':force_style='FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=34'[v];[1:a]apad=pad_dur=115[a]"     -map "[v]" -map "[a]" -t 115 -c:v libx264 -preset veryfast -crf 21 -c:a aac -b:a 128k -movflags +faststart -pix_fmt yuv420p     submission/WEXSPACE_SHIPATON_NEXTGEN_R01.mp4
else
  ffmpeg -hide_banner -loglevel error -y     -i "$OUT/video-silent.mp4"     -vf "subtitles='$OUT/captions.srt':force_style='FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=34'"     -t 115 -c:v libx264 -preset veryfast -crf 21 -movflags +faststart -pix_fmt yuv420p     submission/WEXSPACE_SHIPATON_NEXTGEN_R01.mp4
fi

sha256sum submission/WEXSPACE_SHIPATON_NEXTGEN_R01.mp4 > submission/WEXSPACE_SHIPATON_NEXTGEN_R01.sha256
ffprobe -v error -show_entries format=duration,size -of json submission/WEXSPACE_SHIPATON_NEXTGEN_R01.mp4 > submission/WEXSPACE_SHIPATON_NEXTGEN_R01.meta.json
