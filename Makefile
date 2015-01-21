#########
#
# The top level targets link in the two .o files for now.
#
TARGETS += opc-server

LEDSCAPE_OBJS = ledscape.o pru.o util.o lib/cesanta/frozen.o lib/cesanta/mongoose.o
LEDSCAPE_LIB := libledscape.a

PRU_TEMPLATES := $(wildcard pru/templates/*.p)
EXPANDED_PRU_TEMPLATES := $(addprefix pru/generated/, $(notdir $(PRU_TEMPLATES:.p=.template)))

all: $(TARGETS) all_pru_templates ledscape.service

CFLAGS += \
	-std=c99 \
	-W \
	-Wall \
	-D_BSD_SOURCE \
	-Wp,-MMD,$(dir $@).$(notdir $@).d \
	-Wp,-MT,$@ \
	-I. \
	-O2 \
	-lm \
	-mtune=cortex-a8 \
	-march=armv7-a \
	-Wunused-parameter \
	-DNS_ENABLE_IPV6 \
	-Wunknown-pragmas \
	-Wsign-compare

LDFLAGS += \

LDLIBS += \
	-lpthread \

COMPILE.o = $(CROSS_COMPILE)gcc $(CFLAGS) -c -o $@ $<
COMPILE.a = $(CROSS_COMPILE)ar crv $@ $^
COMPILE.link = $(CROSS_COMPILE)gcc $(LDFLAGS) -o $@ $^ $(LDLIBS)


#####
#
# The TI "app_loader" is the userspace library for talking to
# the PRU and mapping memory between it and the ARM.
#
LDLIBS += -lprussdrv -lm

#####
#
# The TI PRU assembler looks like it has macros and includes,
# but it really doesn't.  So instead we use cpp to pre-process the
# file and then strip out all of the directives that it adds.
# PASM also doesn't handle multiple statements per line, so we
# insert hard newline characters for every ; in the file.
#
PASM := pasm

pru/generated/%.template: pru/templates/%.p pru/templates/common.p.h
	$(eval TEMPLATE_NAME := $(basename $(notdir $@)))
	mkdir -p pru/generated
	pru/build_template.sh $(TEMPLATE_NAME)
	touch $@
	$(MAKE) `ls pru/generated | egrep '^$(TEMPLATE_NAME).*\.p$$' | sed 's/.p$$/.bin/' | sed -E 's/(.*)/pru\/generated\/\1/'`

all_pru_templates: $(EXPANDED_PRU_TEMPLATES)

%.bin: %.p
	mkdir -p pru/bin
	cd `dirname $@` && gcc -E - < $(notdir $<) | perl -p -e 's/^#.*//; s/;/\n/g; s/BYTE\((\d+)\)/t\1/g' > $(notdir $<).i
	$(PASM) -V3 -b $<.i pru/bin/$(notdir $(basename $@))
	#$(RM) $<.i

%.o: %.c
	$(COMPILE.o)

libledscape.a: $(LEDSCAPE_OBJS)
	$(RM) $@
	$(COMPILE.a)

$(foreach O,$(TARGETS),$(eval $O: $O.o $(LEDSCAPE_OBJS) $(APP_LOADER_LIB)))

$(TARGETS):
	$(COMPILE.link)

ledscape.service: ledscape.service.in
	sed 's%LEDSCAPE_PATH%'`pwd`'%' ledscape.service.in > ledscape.service

.PHONY: clean

clean:
	rm -rf \
		*.o \
		*.i \
		.*.o.d \
		*~ \
		$(INCDIR_APP_LOADER)/*~ \
		$(TARGETS) \
		*.bin \
		lib/cesanta/.*.o.d \
		lib/cesanta/*.i \
		lib/cesanta/*.o \
		pru/generated \
		pru/bin \
		ledscape.service
	cd am335x/app_loader/interface && $(MAKE) clean
	cd am335x/pasm && $(MAKE) clean

###########
#
# The correct way to reserve the GPIO pins on the BBB is with the
# capemgr and a Device Tree file.  But it doesn't work.
#
dts: LEDscape.dts
	dtc -O dtb -o BB-LEDSCAPE-00A0.dtbo -b 0 -@ LEDscape.dts
	install	-m 444 BB-LEDSCAPE-00A0.dtbo /lib/firmware
	config-pin overlay BB-LEDSCAPE

# Include all of the generated dependency files
-include .*.o.d
