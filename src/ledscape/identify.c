/** \file
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

extern int width;
extern int height;
uint32_t * demo_identify_p;

void demo_identify_init(void)
{
	int scroll_x = 128;
	demo_identify_p = calloc(width*height,4);
	uint32_t * p = demo_identify_p;
	int pw = width/32;
	printf("numer of panels wide = %d\n", pw);
	memset(p, 0x10, width*height*4);

	for (int i = 0 ; i < 8; i++)
	{
		for (int j = 0 ; j < pw; j++)
		{
			ledscape_printf(
				&p[8+j*32 + width*i*16],
				width,
				0xFF0000, // red
				"%d-%d",
				i,
				j
			);
			ledscape_printf(
				&p[1+j*32 + width*i*16],
				width,
				0x00FF00, // green
				"^"
			);
			ledscape_printf(
				&p[1+j*32 + width*(i*16+8)],
				width,
				0x0000FF, // blue
				"|"
			);
			p[j*32+width*i*16] = 0xFFFF00;
		}
	}
}

void demo_identify_update(
	ledscape_t * const leds
)
{
	ledscape_draw(leds, demo_identify_p);
	usleep(20000);
}

