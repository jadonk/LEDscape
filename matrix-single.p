// \file
 /* PRU based 16x32 LED Matrix driver.
 *
 * Drives up to sixteen 16x32 matrices using the PRU hardware.
 *
 * Uses sixteen data pins in GPIO0 (one for each data line on each
 * matrix) and six control pins in GPIO1 shared between all the matrices.
 *
 * The ARM writes a 24-bit color 512x16 into the shared RAM, sets the
 * frame buffer pointer in the command structure and the PRU clocks it out
 * to the sixteen matrices.  Since there is no PWM in the matrix hardware,
 * the PRU will cycle through various brightness levels. After each PWM
 * cycle it rechecks the frame buffer pointer, allowing a glitch-free
 * transition to a new frame.
 *
 * To pause the redraw loop, write a NULL to the buffer pointer.
 * To shut down the PRU, write -1 to the buffer pointer.
 */
#define r11_gpio 2
#define r11_pin 2
#define g11_gpio 2
#define g11_pin 3
#define b11_gpio 2
#define b11_pin 5

#define r12_gpio 0
#define r12_pin 23
#define g12_gpio 2
#define g12_pin 4
#define b12_gpio 0
#define b12_pin 26

#define CAT3(X,Y,Z) X##Y##Z

// Control pins are all in GPIO1
#define gpio1_sel0 12 /* must be sequential with sel1 and sel2 */
#define gpio1_sel1 13
#define gpio1_sel2 14
#define gpio1_sel3 15
#define gpio1_latch 28
#define gpio1_oe 29
#define gpio1_clock 19

/** Generate a bitmask of which pins in GPIO0-3 are used.
 * 
 * \todo wtf "parameter too long": only 128 chars allowed?
 */

#define GPIO1_SEL_MASK (0\
|(1<<gpio1_sel0)\
|(1<<gpio1_sel1)\
|(1<<gpio1_sel2)\
|(1<<gpio1_sel3)\
)

.origin 0
.entrypoint START

#include "ws281x.hp"

/** Mappings of the GPIO devices */
#define GPIO0 (0x44E07000 + 0x100)
#define GPIO1 (0x4804c000 + 0x100)
#define GPIO2 (0x481AC000 + 0x100)
#define GPIO3 (0x481AE000 + 0x100)

/** Offsets for the clear and set registers in the devices.
 * Since the offsets can only be 0xFF, we deliberately add offsets
 */
#define GPIO_CLRDATAOUT (0x190 - 0x100)
#define GPIO_SETDATAOUT (0x194 - 0x100)

/** Register map */
#define data_addr r0
#define width r1
#define row r2
#define bright r3
#define offset r4
#define out_clr r5 // must be one less than out_set
#define out_set r6
#define gpio0_set r6 // overloaded with out_set
#define gpio1_set r7
#define gpio2_set r8
#define gpio3_set r9
#define gpio0_led_mask r10
#define gpio1_led_mask r11
#define gpio2_led_mask r13
#define gpio3_led_mask r14
#define clock_pin r15
#define gpio0_base r16
#define gpio1_base r17
#define gpio2_base r18
#define gpio3_base r19
#define pixel_data r20 // the next 12 registers, too

#define BRIGHT_STEP 2

#define CLOCK_LO \
        SBBO clock_pin, gpio1_base, GPIO_SETDATAOUT, 4; \

#define CLOCK_HI \
        SBBO clock_pin, gpio1_base, GPIO_CLRDATAOUT, 4; \

#define LATCH_HI \
	MOV out_set, 1 << gpio1_latch; \
        SBBO out_set, gpio1_base, GPIO_SETDATAOUT, 4; \

#define LATCH_LO \
	MOV out_clr, 1 << gpio1_latch; \
        SBBO out_clr, gpio1_base, GPIO_CLRDATAOUT, 4; \

#define DISPLAY_OFF \
	MOV out_set, 1 << gpio1_oe; \
	SBBO out_set, gpio1_base, GPIO_SETDATAOUT, 4; \

#define DISPLAY_ON \
	MOV out_set, 1 << gpio1_oe; \
	SBBO out_set, gpio1_base, GPIO_CLRDATAOUT, 4; \


START:
    // Enable OCP master port
    // clear the STANDBY_INIT bit in the SYSCFG register,
    // otherwise the PRU will not be able to write outside the
    // PRU memory space and to the BeagleBon's pins.
    LBCO	r0, C4, 4, 4
    CLR		r0, r0, 4
    SBCO	r0, C4, 4, 4

    // Configure the programmable pointer register for PRU0 by setting
    // c28_pointer[15:0] field to 0x0120.  This will make C28 point to
    // 0x00012000 (PRU shared RAM).
    MOV		r0, 0x00000120
    MOV		r1, CTPPR_0
    ST32	r0, r1

    // Configure the programmable pointer register for PRU0 by setting
    // c31_pointer[15:0] field to 0x0010.  This will make C31 point to
    // 0x80001000 (DDR memory).
    MOV		r0, 0x00100000
    MOV		r1, CTPPR_1
    ST32	r0, r1

    // Write a 0x1 into the response field so that they know we have started
    MOV r2, #0x1
    SBCO r2, CONST_PRUDRAM, 12, 4

    // Wait for the start condition from the main program to indicate
    // that we have a rendered frame ready to clock out.  This also
    // handles the exit case if an invalid value is written to the start
    // start position.

        MOV gpio0_base, GPIO0
        MOV gpio1_base, GPIO1
        MOV gpio2_base, GPIO2
        MOV gpio3_base, GPIO3

        MOV gpio0_led_mask, 0
        MOV gpio1_led_mask, 0
        MOV gpio2_led_mask, 0
        MOV gpio3_led_mask, 0

#define GPIO_MASK(X) CAT3(gpio,X,_led_mask)
	SET GPIO_MASK(r11_gpio), r11_pin
	SET GPIO_MASK(g11_gpio), g11_pin
	SET GPIO_MASK(b11_gpio), b11_pin
	SET GPIO_MASK(r12_gpio), r12_pin
	SET GPIO_MASK(g12_gpio), g12_pin
	SET GPIO_MASK(b12_gpio), b12_pin

        MOV clock_pin, 1 << gpio1_clock

READ_LOOP:
        // Load the pointer to the buffer from PRU DRAM into r0 and the
        // length (in pixels) into r1.
        LBCO      data_addr, CONST_PRUDRAM, 0, 8

        // Wait for a non-zero command
        QBEQ READ_LOOP, data_addr, #0

        // Command of 0xFF is the signal to exit
        QBEQ EXIT, data_addr, #0xFF

	// scale the width into number of bytes that we will read
	// 16 outputs * 3 bytes per output
/********
	ADD offset, width, width
	ADD offset, offset, width
	LSL width, offset, 4
*/

        MOV row, 0

NEW_ROW_LOOP:
		// Disable output while we set the address
		DISPLAY_OFF

		// set address; select pins in gpio1 are sequential
		// xor with the select bit mask to set which ones should
		LSL out_set, row, gpio1_sel0
		MOV out_clr, GPIO1_SEL_MASK
		AND out_set, out_set, out_clr // ensure no extra bits
		XOR out_clr, out_clr, out_set // complement the bits into clr
		SBBO out_clr, gpio1_base, GPIO_CLRDATAOUT, 8 // set both

		MOV bright, 0x100
	ROW_LOOP:
		// Re-start reading at the same row
		MOV offset, 0

		// Reset the latch pin; will be toggled at the end of the row
		LATCH_LO

		// compute where we are in the image
		PIXEL_LOOP:
			// Load the sixteen RGB outputs into
			// consecutive registers, starting at pixel_data.
			// This takes about 250 ns
			LBBO pixel_data, data_addr, offset, 3*2

			CLOCK_HI

			MOV gpio0_set, 0
			MOV gpio1_set, 0
			MOV gpio2_set, 0
			MOV gpio3_set, 0
#define GPIO(R) CAT3(gpio,R,_set)
#define OUTPUT_ROW(N,reg_r,reg_g,reg_b) \
	QBGE skip_r##N, reg_r, bright; \
	SET GPIO(r##N##_gpio), r##N##_pin; \
	skip_r##N: \
	QBGE skip_g##N, reg_g, bright; \
	SET GPIO(g##N##_gpio), g##N##_pin; \
	skip_g##N: \
	QBGE skip_b##N, reg_b, bright; \
	SET GPIO(b##N##_gpio), b##N##_pin; \
	skip_b##N: \

            //MOV r21.b1, 0x21
			OUTPUT_ROW(11, r20.b0, r20.b1, r20.b2)
			OUTPUT_ROW(12, r20.b3, r21.b0, r21.b1)
            //SET GPIO(b12_gpio), b12_pin

			// All bits are configured;
			// the non-set ones will be cleared
			// We write 8 bytes since CLR and DATA are contiguous,
			// which will write both the 0 and 1 bits in the
			// same instruction.  gpio0 and out_set are the same
			// register, so they must be done first.
			AND out_set, gpio0_set, gpio0_led_mask
			XOR out_clr, out_set, gpio0_led_mask
			SBBO out_clr, gpio0_base, GPIO_CLRDATAOUT, 8

			AND out_set, gpio1_set, gpio1_led_mask
			XOR out_clr, out_set, gpio1_led_mask
			SBBO out_clr, gpio1_base, GPIO_CLRDATAOUT, 8

			AND out_set, gpio2_set, gpio2_led_mask
			XOR out_clr, out_set, gpio2_led_mask
			SBBO out_clr, gpio2_base, GPIO_CLRDATAOUT, 8

			AND out_set, gpio3_set, gpio3_led_mask
			XOR out_clr, out_set, gpio3_led_mask
			SBBO out_clr, gpio3_base, GPIO_CLRDATAOUT, 8

			CLOCK_LO

#if 1
			// If the brightness is less than the pixel, turn off
			// but keep in mind that this is the brightness of
			// the previous row, not this one.
			LSR out_set, offset, 0
			ADD out_clr, bright, 10
			LSL out_clr, out_clr, 4

			QBLT no_blank, out_clr, out_set
			DISPLAY_OFF
			no_blank:
#endif

			ADD offset, offset, 3*2
			QBNE PIXEL_LOOP, offset, width

		// Full data has been clocked out; latch it
		LATCH_HI
		DISPLAY_ON

		// Update the brightness, and then give the row another scan
		SUB bright, bright, BRIGHT_STEP
		QBLT ROW_LOOP, bright, 0

		// We have just done all eight brightness levels for this
		// row.  Time to move to the new row

		// Increment our data_offset to point to the next row
		ADD data_addr, data_addr, offset

                ADD row, row, 1
                QBEQ READ_LOOP, row, 8

		QBA NEW_ROW_LOOP
	
EXIT:
#ifdef AM33XX
    // Send notification to Host for program completion
    MOV R31.b0, PRU0_ARM_INTERRUPT+16
#else
    MOV R31.b0, PRU0_ARM_INTERRUPT
#endif

    HALT