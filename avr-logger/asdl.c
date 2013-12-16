#include "asdl.h"

/*----------------------------------------------------------------------------*/
void
asdl_add_ch(struct asdl_logger* logger, uint8_t nr, uint8_t type, uint32_t divisor, char* name, char* unit) {
  uint8_t t_size = 0;
  switch(type & 0x07) {
    case ASDL_INT8:
      t_size = 1;
      break;
    case ASDL_INT16:
      t_size = 2;
      break;
    case ASDL_INT32:
      t_size = 4;
      break;
    case ASDL_INT64:
      t_size = 8;
      break;
    case ASDL_FLOAT:
      t_size = 4;
      break;
    default:
      t_size = 0;
      break;
  }
  // size * vector size
  t_size *= ((type >> 4) + 1);

  logger->channels[nr].type = type;
  logger->channels[nr].t_size = t_size;
  logger->channels[nr].divisor = divisor;
  logger->channels[nr].name = name;
  logger->channels[nr].unit = unit;
  // send out channel information
  logger->send(ASDL_IDENTIFIER);
  logger->send(ASDL_CMD_ADD | nr);
  logger->send(type);
  logger->send((divisor >> 24) & 0xFF);
  logger->send((divisor >> 16) & 0xFF);
  logger->send((divisor >> 8) & 0xFF);
  logger->send((divisor >> 0) & 0xFF);
  while (*name) {
    logger->send(*name++);
  }
  logger->send('\0');
  while (*unit) {
    logger->send(*unit++);
  }
  logger->send('\0');
  logger->send(ASDL_END_TOKEN);
}
/*----------------------------------------------------------------------------*/
void
asdl_start_logger(struct asdl_logger* logger) {
  logger->send(ASDL_IDENTIFIER);
  logger->send(ASDL_CMD_GO);
  logger->send(ASDL_END_TOKEN);
}
/*----------------------------------------------------------------------------*/
void
asdl_log(struct asdl_logger* logger, uint8_t nr, void *value) {
  uint8_t idx = 0;
  logger->send(ASDL_IDENTIFIER);
  logger->send(ASDL_CMD_DATA | nr);
  // send payload byte per byte
  uint8_t val = 0;
  for (idx = 0; idx < logger->channels[nr].t_size; idx++) {
    val = *(((char*) value) + idx);
    logger->send(*(((char*) value) + idx));
  }
  logger->send(ASDL_END_TOKEN);
}
/*----------------------------------------------------------------------------*/

