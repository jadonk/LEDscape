/** \file
 *  UDP image packet receiver.
 *
 * Based on the HackRockCity LED Display code:
 * https://github.com/agwn/pyramidTransmitter/blob/master/LEDDisplay.pde
 *
 * Designed to render into the LED matrix.
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>
#include <fcntl.h>
#include <termios.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <inttypes.h>
#include <errno.h>
#include <string.h>
#include <pthread.h>
#include <getopt.h>
#include "util.h"
#include "ledscape.h"

static int verbose;
unsigned width = 256;
unsigned height = 256;
int port = 9999;

extern void demo_matrix_test_init(void);
extern void demo_matrix_test_update(
	ledscape_t * const leds
);
extern void demo_identify_init(void);
extern void demo_identify_update(
	ledscape_t * const leds
);

static int
udp_socket(
	const int port
)
{
	const int sock = socket(AF_INET, SOCK_DGRAM, 0);
	struct sockaddr_in addr = {
		.sin_family = AF_INET,
		.sin_port = htons(port),
		.sin_addr.s_addr = INADDR_ANY,
	};

	if (sock < 0)
		return -1;
	if (bind(sock, (const struct sockaddr*) &addr, sizeof(addr)) < 0)
		return -1;

	return sock;
}


static int
wait_socket(
	int fd,
	int msec_timeout
)
{
	struct timeval tv = { msec_timeout / 1000, msec_timeout % 1000 };
	fd_set fds;
	FD_ZERO(&fds);
	FD_SET(fd, &fds);
	return select(fd+1, &fds, NULL, NULL, &tv);
}


static struct option long_options[] =
{
	/* These options set a flag. */
	{"verbose", no_argument,       0, 1},
	{"port",    required_argument, 0, 'p'},
	{"width",   required_argument, 0, 'W'},
	{"height",  required_argument, 0, 'H'},
	{"config",  required_argument, 0, 'c'},
	{"timeout", required_argument, 0, 't'},
	{"message", required_argument, 0, 'm'},
	{"noinit",  no_argument,       0, 'n'},
	{0, 0, 0, 0}
};


static void usage(void)
{
	fprintf(stderr, "usage not yet written\n");
	exit(EXIT_FAILURE);
}

char * startup_message = "See http://ow.ly/zsuPi";
static void display_startup_message(ledscape_t * const leds)
{
	static int init = 0;
	static uint32_t * fb;
	if(!init) {
		fb = calloc(width*height,4);
		ledscape_printf(fb+0*width, width, 0xFF0000, "%s", startup_message);
		ledscape_printf(fb+16*width, width, 0x00FF00, "%dx%d UDP port %d", width, height, port);
	}
	ledscape_draw(leds, fb);

	sleep(1);
}

static void display_failure(ledscape_t * const leds, const char * message)
{
	uint32_t * const fb = calloc(width*height,4);
	memset(fb, 0, width*height*4);
	ledscape_printf(fb, width, 0xFF0000, message);
	ledscape_draw(leds, fb);
	free(fb);
}

int
main(
	int argc,
	char ** argv
)
{
	/* getopt_long stores the option index here. */
	int option_index = 0;
	const char * config_file = NULL;
	int timeout = 60;
	int no_init = 0;

	while (1)
	{
		const int c = getopt_long(
			argc,
			argv,
			"vp:c:t:W:H:m:n",
			long_options,
			&option_index
		);

		if (c == -1)
			break;
		switch (c)
		{
		case 'v':
			verbose++;
			break;
		case 'n':
			no_init++;
			break;
		case 'c':
			config_file = optarg;
			break;
		case 't':
			timeout = atoi(optarg);
			break;
		case 'W':
			width = atoi(optarg);
			break;
		case 'H':
			height = atoi(optarg);
			break;
		case 'm':
			startup_message = optarg;
			break;
		default:
			usage();
			return -1;
		}
	}

	const int sock = udp_socket(port);
	if (sock < 0)
		die("socket port %d failed: %s\n", port, strerror(errno));

	const size_t image_size = width * height * 3;

	// largest possible UDP packet
	uint8_t *buf = calloc(65536,1);
#if 0
	if (sizeof(buf) < image_size + 1)
		die("%u x %u too large for UDP\n", width, height);
#endif

	fprintf(stderr, "%u x %u, UDP port %u\n", width, height, port);

	ledscape_config_t * config = &ledscape_matrix_default;
	if (config_file)
	{
		config = ledscape_config(config_file);
		if (!config)
			return EXIT_FAILURE;
	}

	if (config->type == LEDSCAPE_MATRIX)
	{
		config->matrix_config.width = width;
		config->matrix_config.height = height;
	}

	ledscape_t * const leds = ledscape_init(config, no_init);
	if (!leds)
		return EXIT_FAILURE;

	const unsigned report_interval = 10;
	unsigned last_report = 0;
	unsigned long delta_sum = 0;
	unsigned frames = 0;
	unsigned mode = 0x30;

	demo_matrix_test_init();
	demo_identify_init();

	display_startup_message(leds);
	uint32_t * const fb = calloc(width*height,4);
	while (1)
	{
		const ssize_t rlen = recv(sock, buf, 65536, MSG_DONTWAIT);
		if (rlen > 0) {
			warn_once("received %zu bytes\n", rlen);
			mode = buf[0];
		}

		switch(mode)
		{
		case 0:
		case 1:
		case 2:
		case 3:
			// copy the 3-byte values into the 4-byte framebuffer
			// and turn onto the side
			for (unsigned x = 0 ; x < width ; x++) // 256
			{
				for (unsigned y = 0 ; y < 64 ; y++) // can only fit 256x64
				{
					uint32_t * out = (void*) &fb[(y+64*mode)*width + x];
					const uint8_t * const in = &buf[1 + 3*(y*width + x)];
					uint32_t r = in[0];
					uint32_t g = in[1];
					uint32_t b = in[2];
					*out = (r << 16) | (g << 8) | (b << 0);
				}
			}

			ledscape_draw(leds, fb);
			break;

		case 0x30:
			display_startup_message(leds);
			break;

		case 0x31:
			demo_matrix_test_update(leds);
			break;

		case 0x32:
			demo_identify_update(leds);
			break;

		default:
			printf("bad type %d\n", mode);
			mode = 0x30;
			break;
		}
	}

	return 0;
}
