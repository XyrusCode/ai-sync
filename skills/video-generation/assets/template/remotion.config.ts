import {Config} from '@remotion/cli/config';

// jpeg frames render faster than png and are plenty for h264 output.
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
