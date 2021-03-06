#!/usr/bin/env python

import sys
import math
from gnuradio import gr, gru, audio, eng_notation, blocks, filter
from gnuradio import audio
from gnuradio.eng_option import eng_option
from gnuradio.wxgui import stdgui2, fftsink2
from optparse import OptionParser

try:
    import cqpsk
except:
    from tetra_demod import cqpsk

# applies frequency translation, resampling (interpolation/decimation) and cqpsk demodulation

class my_top_block(stdgui2.std_top_block):
    def __init__(self, frame, panel, vbox, argv):
        stdgui2.std_top_block.__init__(self, frame, panel, vbox, argv)

	self.frame = frame
	self.panel = panel

	options = get_options()

	sample_rate = int(options.sample_rate)	

	self.asrc = audio.source(sample_rate, options.audio_device, True)

	self.f2c = blocks.float_to_complex(1)

	self.connect((self.asrc, 1), (self.f2c, 1))
	self.connect((self.asrc, 0), (self.f2c, 0))

        symbol_rate = 18000
        sps = 2
        # output rate will be 36,000
        ntaps = 11 * sps
        new_sample_rate = symbol_rate * sps

        channel_taps = filter.firdes.low_pass(1.0, sample_rate, options.low_pass, options.low_pass * 0.1, filter.firdes.WIN_HANN)

        FILTER = filter.freq_xlating_fir_filter_ccf(1, channel_taps, options.calibration, sample_rate)

        sys.stderr.write("sample rate: %d\n" %(sample_rate))

        DEMOD = cqpsk.cqpsk_demod( samples_per_symbol = sps,
                                 excess_bw=0.35,
                                 costas_alpha=0.03,
                                 gain_mu=0.05,
                                 mu=0.05,
                                 omega_relative_limit=0.05,
                                 log=options.log,
                                 verbose=options.verbose)

        OUT = blocks.file_sink(gr.sizeof_float, options.output_file)

        r = float(sample_rate) / float(new_sample_rate)

        INTERPOLATOR = filter.fractional_interpolator_cc(0, r)

        self.connect(self.f2c, FILTER, INTERPOLATOR, DEMOD, OUT)

	self.scope = fftsink2.fft_sink_c(panel, fft_size=512,
					 sample_rate=sample_rate,
					 ref_scale=2.0,
					 ref_level=-30, y_divs=10,
					 fft_rate=10,
					 average=True,
					 avg_alpha=0.2)
	self.connect(self.f2c, self.scope)

def get_options():
    parser = OptionParser(option_class=eng_option)

    parser.add_option("-r", "--sample-rate", type="eng_float", default=96000,
	          help="set sample rate to RATE (96000)")
    parser.add_option("-D", "--audio-device", type="string", default="",
	          help="pcm input device name.  E.g., hw:0,0 or /dev/dsp")

    # demodulator related settings
    parser.add_option("-c", "--calibration", type="int", default=0, help="freq offset")
    parser.add_option("-l", "--log", action="store_true", default=False, help="dump debug .dat files")
    parser.add_option("-L", "--low-pass", type="eng_float", default=25e3, help="low pass cut-off", metavar="Hz")
    parser.add_option("-o", "--output-file", type="string", default="out.float", help="specify the bit output file")
    parser.add_option("-v", "--verbose", action="store_true", default=False, help="dump demodulation data")
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.print_help()
        raise SystemExit, 1

    return (options)

if __name__ == "__main__":
    app = stdgui2.stdapp(my_top_block, "OsmoTETRA FCDP", nstatus=1)
    app.MainLoop()
