/** \file
 * Test the matrix LCD PRU firmware with a multi-hue rainbow.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <inttypes.h>
#include <errno.h>
#include <unistd.h>
#include "ledscape.h"


int
main(void)
{
	const int width = 32*5;
	const int height = 16;
	unsigned i;
	uint32_t * const p = calloc(width*height,4);

	ledscape_t * const leds = ledscape_init(width, height);
	printf("init done\n");

	for(i = 0; i < width*height; i++) {
		p[i] = 0x002f0f5f;
	}
	ledscape_draw(leds, p);

	ledscape_close(leds);

	return EXIT_SUCCESS;
}
