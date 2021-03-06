The `PixelFormats` enum is basically copied from `misctools/DPGTools/sources.zip`
in the MoonShell package, from the `_dpg_const.pas` file:

	const DPGPixelFormat_RGB15=0;
	const DPGPixelFormat_RGB18=1;
	const DPGPixelFormat_RGB21=2;
	const DPGPixelFormat_RGB24=3;
	const DPGPixelFormat_ENUMCOUNT=4;

This, however, must be somehow incorrect or incomplete, because the MPEG-1 codec
does not support RGB pixel formats:

- ffmpeg help: `ffmpeg -h encoder=mpeg1video`
- [MPEG-1 color space on Wikipedia](https://en.wikipedia.org/wiki/MPEG-1#Color_space)

Other DPG conversion tools handle the pixel format by adding a video format
filter to mencoder options (note the comment about "not really working"):

DPG for X:

	    # Prepare the pixel format string
	    # Does this really work for anyone? Not for me!
	    if Globals.video_pixel == 3:
	        v_pixelformat = "format=rgb24"
	    elif Globals.video_pixel == 2:
	        v_pixelformat = "format=rgb21"
	    elif Globals.video_pixel == 1:
	        v_pixelformat = "format=rgb18"
	    elif Globals.video_pixel == 0:
	        v_pixelformat = "format=rgb15"

dpgconv:

		if ((options.dpg == 0) | (options.dpg == 4)):
			v_pf = "format=rgb24,"
			options.pf = 3
		elif options.pf == 3:
			v_pf = "format=rgb24,"
		elif options.pf == 2:
			v_pf = "format=rgb21,"
		elif options.pf == 1:
			v_pf = "format=rgb18,"
		elif options.pf == 0:
			v_pf = "format=fmt=rgb15,"
		else:
			v_pf = "format=rgb24,"
			options.pf = 3

This has no effect on the output pixel format, which is always yuv420p.
Verify by running:

	mencoder 'tests/samples/Test Image - 2141.mp4' -really-quiet \
	-vf format=rgb24,scale=256:192:::3,harddup -nosound -ovc lavc \
	-lavcopts vcodec=mpeg1video -o - -of rawvideo | ffprobe -

Relevant part of the output:

	Stream #0:0: Video: mpeg1video, yuv420p(tv),

On the other hand, the utilities included with MoonShell do not set the pixel
format when reencoding. Because of this, neither does dpgv4. The inexplicable
RGB24 value still needs to go into the DPG header, though.
