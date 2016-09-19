
setlocal EnableDelayedExpansion

for /F "tokens=1 delims=." %%a in ("%1") do (
      set filename=%%a
)
for /F "tokens=2 delims=." %%a in ("%1") do (
      set startfr=%%a
)
for /F "tokens=3 delims=." %%a in ("%1") do (
      set extn=%%a
)

C:\code\bin\utils\win\ffmpeg\20160725\bin\ffmpeg.exe -start_number %startfr% -i %filename%.%%04d.%extn% -s 1280x720 -vcodec libx264 -b:v 8000k -vf format=yuv420p -r 24 %filename%_h264.mp4