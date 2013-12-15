#ifndef __ASDL_H__
#define __ASDL_H__

#include <stdio.h>

// AVR serial data logger
struct asdl_logger {
  uint8_t nr_chs;
  char* name;
  struct asdl_channel* channels;
  void (*send)(char);
};

#define INT8   1
#define INT32  4

/* Data type encoding */
// 3 byte type
#define ASDL_INT8     (0 << 0)
#define ASDL_INT16    (1 << 0)
#define ASDL_INT32    (2 << 0)
#define ASDL_INT64    (3 << 0)
#define ASDL_FLOAT    (4 << 0)
// 1 bit signedness info
#define ASDL_SIGNED   (0 << 1)
#define ASDL_UNSIGNED (1 << 1)
// upper 4 byte : vector size - 1 
#define ASDL_VEC1     (0 << 4)
#define ASDL_VEC2     (1 << 4)
#define ASDL_VEC3     (2 << 4)
#define ASDL_VEC4     (3 << 4)
#define ASDL_VEC5     (4 << 4)
#define ASDL_VEC6     (5 << 4)
// ...


struct asdl_channel {
  // mask that specifies data type
  uint8_t type;
  // size of type, calculated by asdl_add_ch()
  uint8_t t_size;
  // allows to set divisor for data interpretation, related to 'unit'
  uint32_t divisor;
  char* name; 
  char* unit;
};

#define ASDL_IDENTIFIER 0x55
#define ASDL_END_TOKEN  0x69

#define ASDL_CMD_DATA 0x00
#define ASDL_CMD_ADD  0x10
#define ASDL_CMD_GO   0x20

/** 
 * \defgroup asdl AVR serial data logger
 *
 *
 * \section protocol Protocol specification
 *
 * Header byte (0x55) identifies start of any command
 *
 * ch_nr    number of this channel
 * ch_type  tells receiver how to decode data or this channel
 *          byte is assembled as follows [ vector size (4) | signedness (1) | type ],
 *          where type can be INT8, INT16, FLOAT, ...
 * ch_divisor sets a divisor to apply at receiver site to match ch_unit
 * ch_name  is the name of the channel, e.g. "Acc x"
 * ch_unit  is the unit of the channel, e.g. "mg"
 * setup: [ header byte | cmd+ch_nr | ch_type | ch_name | ch_unit | end token ]
 *
 * Example:
 * [ 0x55 | 0 | UINT32 | "Acc x" | "mg" | 0x69 ]
 * [ 0x55 | 1 | UINT32 | "Acc y" | "mg" | 0x69 ]
 * [ 0x55 | 2 | UINT32 | "Acc z" | "mg" | 0x69 ]
 * [ 0x55 | 3 | UINT16 | "Temp"  | "C"  | 0x69 ]
 *
 * 
 * header byte identifies start of data
 * id allows receiver to assign data a set up stream
 * data bytes contain payload
 * format: [ header byte | cmd+ch_nr | x data bits | end token ]
 *
 * @{ */

/**
 * Adds a data channel
 *
 * @param logger
 * @param nr
 * @param type
 * @param divisor
 * @param name
 * @param unit
 */
void asdl_add_ch(struct asdl_logger* logger, uint8_t nr, uint8_t type, uint32_t divisor, char* name, char* unit);

/**
 * Tells the logger to start.
 *
 * @param logger
 */
void asdl_start_logger(struct asdl_logger* logger);

/**
 * Send log data of data channel.
 *
 * @param logger
 * @param nr
 * @param value
 */
void asdl_log(struct asdl_logger* logger, uint8_t nr, void *value);

/*
#define CREATE_CHANNEL(nr, type, name, unit) \
  struct asdl_channel channel##nr## = { \
    type, name, unit
  }
*/

#define CREATE_LOGGER(name, desc, channels, func) \
  struct asdl_channel ch_##name[channels]; \
  struct asdl_logger name = { channels, desc, ch_##name, func}

/** @} */

#endif

