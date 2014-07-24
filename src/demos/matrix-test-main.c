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

int width = 256;
int height = 256;

int
main(
	int argc,
	const char ** argv
)
{
	ledscape_config_t * config = &ledscape_matrix_default;
	if (argc > 1)
	{
		config = ledscape_config(argv[1]);
		if (!config)
			return EXIT_FAILURE;
	}

	if (config->type == LEDSCAPE_MATRIX)
	{
		config->matrix_config.width = width;
		config->matrix_config.height = height;
	}

	ledscape_t * const leds = ledscape_init(config, 0);

	printf("init done\n");

	demo_matrix_test_init();
	
	while (1)
	{
		demo_matrix_test_update(leds);
	}

	ledscape_close(leds);

	return EXIT_SUCCESS;
}
