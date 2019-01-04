# MPEG-1 framerates

| frames/seconds | as float | index | ffmpeg abbreviations | in spec? | comments
| -------------- | -------- | ----- | -------------------- | -------- | ---------------------------------------------------
|   24000/1001   |  23.976  |    1  | ntsc-film            |    YES   | 3-2 pulldown NTSC
|      24/1      |  24      |    2  | film                 |    YES   | film
|      25/1      |  25      |    3  | pal qpal spal        |    YES   | PAL/SECAM or 625/60 video
|   30000/1001   |  29.97   |    4  | ntsc qntsc sntsc     |    YES   | NTSC
|      30/1      |  30      |    5  |                      |    YES   | drop-frame NTSC or component 525/60
|      50/1      |  50      |    6  |                      |    YES   | double-rate PAL
|   60000/1001   |  59.94   |    7  |                      |    YES   | double rate NTSC
|      60/1      |  60      |    8  |                      |    YES   | double-rate, drop-frame NTSC/component 525/60 video
|      15/1      |  15      |    9  |                      |     NO   | Xing's 15fps
|       5/1      |   5      |   10  |                      |     NO   | libmpeg3's "Unofficial economy rates"
|      10/1      |  10      |   11  |                      |     NO   | libmpeg3's "Unofficial economy rates"
|      12/1      |  12      |   12  |                      |     NO   | libmpeg3's "Unofficial economy rates"
|      15/1      |  15      |   13  |                      |     NO   | libmpeg3's "Unofficial economy rates"

ffmpeg will not accept framerates that are not part of the official spec
unless standards compliance is set to `FF_COMPLIANCE_UNOFFICIAL` or lower
(`-strict unofficial` or `-strict experimental`).

The "index" column contains the value used in the MPEG video sequence header
(lower half of the 4th byte in sequence header / 8th byte in stream, if you
count bytes starting from 1).

For dpgv4 framerate can be specified using values from the "as float" column.

Sources:

- ffmpeg help: `ffmpeg -h encoder=mpeg1video`
- ffmpeg source code:
	- the `ff_mpeg12_frame_rate_tab` table in `libavcodec/mpeg12framerate.c`
	- the `find_frame_rate_index` function in `libavcodec/mpeg12enc.c`
- [ffmpeg documentation](http://ffmpeg.org/ffmpeg-utils.html#Video-rate)
- [MPEG-FAQ](http://www.faqs.org/faqs/mpeg-faq/part3/)
- [MPEG Headers Quick Reference](http://dvd.sourceforge.net/dvdinfo/mpeghdrs.html)
