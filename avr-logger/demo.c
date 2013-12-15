#include "asdl.h"
#include "contiki.h"
#include <stdio.h> /* For printf() */
#include "rs232.h"

// allows to send data via rs232
void my_send(char dat) {
  rs232_send(RS232_PORT_0, (unsigned char) dat);
}

/*---------------------------------------------------------------------------*/
PROCESS(hello_world_process, "Hello world process");
AUTOSTART_PROCESSES(&hello_world_process);
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(hello_world_process, ev, data)
{
  PROCESS_BEGIN();

  static struct etimer et;

  while(1)
  {

    // Example:
    CREATE_LOGGER(my_logger, "My Logger", 4, &my_send);
    //struct asdl_channel my_logger_channels[4];
    //struct asdl_logger my_logger = { 4, "My Logger", &my_logger_channels};
    asdl_add_ch(&my_logger, 0, ASDL_VEC3 | ASDL_SIGNED | ASDL_INT32, 1, "Acc  [x:y:z]", "mg");
    asdl_add_ch(&my_logger, 1, ASDL_VEC2 | ASDL_SIGNED | ASDL_INT32, 1, "Gyro [x:y]", "mdps");
    asdl_add_ch(&my_logger, 2, ASDL_VEC1 | ASDL_SIGNED | ASDL_INT16, 1, "Temp",  "C");

    asdl_start_logger(&my_logger);

    int32_t val0[3] = {123, 234, 345};
    asdl_log(&my_logger, 0, &val0);
    int32_t val1[2];
    asdl_log(&my_logger, 1, &val1);
    int16_t val2;
    asdl_log(&my_logger, 2, &val2);

    etimer_set(&et, CLOCK_SECOND);

    PROCESS_YIELD();
  }


  PROCESS_END();
}
/*---------------------------------------------------------------------------*/

