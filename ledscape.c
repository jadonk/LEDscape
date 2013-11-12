/** \file
 * Userspace interface to the WS281x LED strip driver.
 *
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <inttypes.h>
#include <errno.h>
#include <unistd.h>
#include "ledscape.h"
#include "pru.h"

#define CONFIG_LED_MATRIX


#define ARRAY_COUNT(a) ((sizeof(a) / sizeof(*a)))


/** Command structure shared with the PRU.
 *
 * This is mapped into the PRU data RAM and points to the
 * frame buffer in the shared DDR segment.
 *
 * Changing this requires changes in ws281x.p
 */
typedef struct
{
	// in the DDR shared with the PRU
	uintptr_t pixels_dma;

	// Length in pixels of the longest LED strip.
	unsigned num_pixels;

	// write 1 to start, 0xFF to abort. will be cleared when started
	volatile unsigned command;

	// will have a non-zero response written when done
	volatile unsigned response;
} __attribute__((__packed__)) ws281x_command_t;

typedef struct
{
	uint32_t x_offset;
	uint32_t y_offset;
} led_matrix_t;

#define NUM_MATRIX 2

typedef struct
{
	uint32_t matrix_width; // of a full chain
	uint32_t matrix_height; // number of rows per-output (8 or 16)
	led_matrix_t matrix[NUM_MATRIX];
} led_matrix_config_t;



struct ledscape
{
	ws281x_command_t * ws281x;
	pru_t * pru;
	unsigned width;
	unsigned height;
	unsigned frame_size;
	led_matrix_config_t * matrix;
};


#if 1
/** Retrieve one of the two frame buffers. */
ledscape_frame_t *
ledscape_frame(
	ledscape_t * const leds,
	unsigned int frame
)
{
	if (frame >= 2)
		return NULL;

	return (ledscape_frame_t*)((uint8_t*) leds->pru->ddr + leds->frame_size * frame);
}
#endif


static uint8_t
bright_map(
	uint8_t val
)
{
	return val;
}


static uint8_t *
ledscape_remap(
	ledscape_t * const leds,
	uint8_t * const frame,
	unsigned x,
	unsigned y
)
{
#define CONFIG_ZIGZAG
#ifdef CONFIG_ZIGZAG
	(void) leds;

	// each panel is 16x8
	// vertical panel number is y % 8 (which output line)
	// horizontal panel number is y % (16*8)
	// if y % 2 == 1, map backwards
	const unsigned panel_width = 16;
	const unsigned panel_height = 8;
	unsigned panel_num = x / panel_width;
	unsigned output_line = y / panel_height;
	unsigned panel_x = x % panel_width;
	unsigned panel_y = y % panel_height;
	unsigned panel_offset = panel_y * panel_width;

	// the even lines are forwards, the odd lines go backwards
	if (panel_y % 2 == 0)
	{
		panel_offset += panel_x;
	} else {
		panel_offset += panel_width - panel_x - 1;
	}

	return &frame[(panel_num*128 + panel_offset)*48*3 + output_line];
#else
	return &frame[x*48*3 + y];
#endif
}


/** Translate the RGBA buffer to the correct output type and
 * initiate the transfer of a frame to the LED strips.
 *
 * Matrix drivers shuffle to have consecutive bits, ws281x do bit slicing.
 */
void
ledscape_draw(
	ledscape_t * const leds,
	const void * const buffer
)
{
	static unsigned frame = 0;
	const uint32_t * const in = buffer;
	uint8_t * const out = leds->pru->ddr + leds->frame_size * frame;
    int i, j;

#if 1
    for(i = 0; i < 512; i++) {
        j = ((i << 1) & (512 - 1)) + ((i & 256) ? 1 : 0);
        out[j*3+0] = (in[i] >> 0) & 0xff;
        out[j*3+1] = (in[i] >> 8) & 0xff;
        out[j*3+2] = (in[i] >> 16) & 0xff;
    }

	leds->ws281x->pixels_dma = leds->pru->ddr_addr + leds->frame_size * frame;
	//frame = (frame + 1) & 1;
#else
#ifdef CONFIG_LED_MATRIX
	// matrix packed is:
	// this way the PRU can read all sixteen output pixels in
	// one LBBO and clock them out.
	// there is an array of NUM_MATRIX output coordinates (one for each of
	// the sixteen drivers).
	for (unsigned i = 0 ; i < NUM_MATRIX ; i++)
	{
		const led_matrix_t * const m = &leds->matrix->matrix[i];

		for (uint32_t y = 0 ; y < leds->matrix->matrix_height ; y++)
		{
			const uint32_t * const in_row
				= &in[(y+m->y_offset) * leds->width];
			uint8_t * const out_row
				= &out[y * leds->matrix->matrix_width * 3 * NUM_MATRIX];

			for (uint32_t x = 0 ; x < leds->matrix->matrix_width ; x++)
			{
				const uint8_t * const rgb = (const void*) &in_row[x + m->x_offset];
				uint8_t * const out_rgb = &out_row[(i + x * NUM_MATRIX)*3];
				out_rgb[0] = bright_map(rgb[0]);
				out_rgb[1] = bright_map(rgb[1]);
				out_rgb[2] = bright_map(rgb[2]);
			}
		}
	}
	leds->ws281x->pixels_dma = leds->pru->ddr_addr + leds->frame_size * frame;
	//frame = (frame + 1) & 1;
#else
	// Translate the RGBA frame into G R B, sliced by color
	// only 48 outputs currently supported
	const unsigned pru_stride = 48;
	for (unsigned y = 0 ; y < leds->height ; y++)
	{
		const uint32_t * const row_in = &in[y*leds->width];
		for (unsigned x = 0 ; x < leds->width ; x++)
		{
			uint8_t * const row_out
				= ledscape_remap(leds, out, x, y);
			const uint32_t p = row_in[x];
			row_out[0*pru_stride] = (p >>  8) & 0xFF; // green
			row_out[1*pru_stride] = (p >>  0) & 0xFF; // red
			row_out[2*pru_stride] = (p >> 16) & 0xFF; // blue
		}
	}
	
	// Wait for any current command to have been acknowledged
	while (leds->ws281x->command)
		;

	// Update the pixel data and send the start
	leds->ws281x->pixels_dma
		= leds->pru->ddr_addr + leds->frame_size * frame;
	frame = (frame + 1) & 1;

	// Send the start command
	leds->ws281x->command = 1;
#endif
#endif
}


/** Wait for the current frame to finish transfering to the strips.
 * \returns a token indicating the response code.
 */
uint32_t
ledscape_wait(
	ledscape_t * const leds
)
{
	while (1)
	{
		uint32_t response = leds->ws281x->response;
		if (!response)
			continue;
		leds->ws281x->response = 0;
		return response;
	}
}


ledscape_t *
ledscape_init(
	unsigned width,
	unsigned height
)
{
	pru_t * const pru = pru_init(0);
#ifdef CONFIG_LED_MATRIX
	const size_t frame_size = height * width * 3; //LEDSCAPE_NUM_STRIPS * 4;
#else
	const size_t frame_size = 48 * width * 8 * 3;
#endif

#if 0
	if (2 *frame_size > pru->ddr_size)
		die("Pixel data needs at least 2 * %zu, only %zu in DDR\n",
			frame_size,
			pru->ddr_size
		);
#endif

	ledscape_t * const leds = calloc(1, sizeof(*leds));

	*leds = (ledscape_t) {
		.pru		= pru,
		.width		= width,
		.height		= height,
		.ws281x		= pru->data_ram,
		.frame_size	= frame_size,
		.matrix		= calloc(sizeof(*leds->matrix), 1),
	};

#ifdef CONFIG_LED_MATRIX
	*(leds->matrix) = (led_matrix_config_t) {
		.matrix_width	= 16,
		.matrix_height	= 8,
		.matrix		= {
			{ 0, 0 },
			{ 0, 8 },
		},
	};

	*(leds->ws281x) = (ws281x_command_t) {
		.pixels_dma	= 0, // will be set in draw routine
		.num_pixels	= 192,
		.command	= 0,
		.response	= 0,
	};
#else
	// LED strips, not matrix output
	*(leds->ws281x) = (ws281x_command_t) {
		.pixels_dma	= 0, // will be set in draw routine
		.num_pixels	= width * 8, // panel height
		.command	= 0,
		.response	= 0,
	};
#endif

	printf("num pixels: %d\n", leds->ws281x->num_pixels);


#if 0
	// Configure all of our output pins.
	for (unsigned i = 0 ; i < ARRAY_COUNT(gpios0) ; i++)
		pru_gpio(0, gpios0[i], 1, 0);
	for (unsigned i = 0 ; i < ARRAY_COUNT(gpios1) ; i++)
		pru_gpio(1, gpios1[i], 1, 0);
	for (unsigned i = 0 ; i < ARRAY_COUNT(gpios2) ; i++)
		pru_gpio(2, gpios2[i], 1, 0);
	for (unsigned i = 0 ; i < ARRAY_COUNT(gpios3) ; i++)
		pru_gpio(3, gpios3[i], 1, 0);
#endif

	// Initiate the PRU program
#ifdef CONFIG_LED_MATRIX
	pru_exec(pru, "./matrix-single.bin");
#else
	pru_exec(pru, "./ws281x.bin");
#endif

	// Watch for a done response that indicates a proper startup
	// \todo timeout if it fails
	printf("waiting for response\n");
	while (!leds->ws281x->response)
		;
	printf("got response\n");

	return leds;
}


void
ledscape_close(
	ledscape_t * const leds
)
{
	// Signal a halt command
	leds->ws281x->command = 0xFF;
	pru_close(leds->pru);
}


void
ledscape_set_color(
	ledscape_frame_t * const frame,
	uint8_t strip,
	uint8_t pixel,
	uint8_t r,
	uint8_t g,
	uint8_t b
)
{
	ledscape_pixel_t * const p = &frame[pixel].strip[strip];
	p->r = r;
	p->g = g;
	p->b = b;
}

void
ledscape_set_background(
	ledscape_t * const leds,
	uint8_t r,
	uint8_t g,
	uint8_t b
)
{
	uint8_t * const out = leds->pru->ddr;
    int i;
    for(i = 0; i < leds->ws281x->num_pixels*8; i += 3) {
	    out[i+0] = r;
	    out[i+1] = g;
	    out[i+2] = b;
    }
	leds->ws281x->pixels_dma = leds->pru->ddr_addr;
}

void
ledscape_mytest(
	ledscape_t * const leds
)
{
    static int frame = 0;
    static int brightness = 0xff;
    static int increment = -10;
    int i;
	uint8_t * const out = leds->pru->ddr;
    for(i = 0; i < 512; i++) {
	    //out[i*3+0] = (i & 0x01) ? 0xff : 0;
	    //out[i*3+1] = ((i & 0x01) || (i & 0x80)) ? 0xff : 0;
	    //out[i*3+2] = ((i & 0x01) || (i & 0x40)) ? 0xff : 0;
	    out[i*3+0] = (i == frame) ? brightness : 0;
	    out[i*3+1] = 0xff-brightness;
	    out[i*3+2] = (i == 512-frame) ? brightness : 0;
    }
    frame+=2;
    if(frame==512) frame = 1;
    if(frame>511) frame = 0;
    brightness += increment;
    if(brightness < 0xb0) { increment = 10; brightness = 0xb0; }
    if(brightness > 0xff) { increment = -10; brightness = 0xff; }
	leds->ws281x->pixels_dma = leds->pru->ddr_addr;
}
