#include <stdio.h>

#include "extra.h"
#include "helper.h"

int main(void)
{
    if (OUTPUT_ENABLED) {
        puts(helper_message());
    }
    return 0;
}
