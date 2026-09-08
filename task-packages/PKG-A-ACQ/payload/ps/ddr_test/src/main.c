#include <stdint.h>
#include "xil_printf.h"
#include "xil_cache.h"
#include "xpseudo_asm.h"

extern unsigned char __ddr_test_start[];
extern unsigned char __ddr_test_end[];
extern unsigned char end[];  /* 当前链接脚本：程序、堆栈之后的位置 */

#define MODE_COUNT 5U
#define PRINT_LIMIT 8U

static const char * const mode_names[MODE_COUNT] = {
    "ZERO", "ONES", "AA", "55", "ADDRESS"
};

/* 根据模式和当前地址计算应写入的值。 */
static uint32_t pattern_value(uint32_t mode, uintptr_t address)
{
    switch (mode) {
    case 0U: return 0x00000000U;
    case 1U: return 0xFFFFFFFFU;
    case 2U: return 0xAAAAAAAAU;
    case 3U: return 0x55555555U;
    default: return (uint32_t)address;
    }
}

/* 每种模式：先写满整个区域，再完整读回比较。 */
static uint32_t test_mode(uint32_t mode,
                          uintptr_t start,
                          uint32_t words)
{
    volatile uint32_t * const memory =
        (volatile uint32_t *)start;

    uint32_t errors = 0U;

    xil_printf("\r\n[%u/%u] %s: writing...\r\n",
               (unsigned int)(mode + 1U),
               (unsigned int)MODE_COUNT,
               mode_names[mode]);

    for (uint32_t i = 0U; i < words; i++) {
        const uintptr_t address =
            start + (uintptr_t)i * sizeof(uint32_t);

        memory[i] = pattern_value(mode, address);
    }

    dsb();

    xil_printf("%s: checking...\r\n", mode_names[mode]);

    for (uint32_t i = 0U; i < words; i++) {
        const uintptr_t address =
            start + (uintptr_t)i * sizeof(uint32_t);

        const uint32_t expected = pattern_value(mode, address);
        const uint32_t actual = memory[i];

        if (actual != expected) {
            if (errors < PRINT_LIMIT) {
                xil_printf(
                    "FAIL addr=0x%08x expected=0x%08x actual=0x%08x\r\n",
                    (unsigned int)address,
                    (unsigned int)expected,
                    (unsigned int)actual);
            }
            errors++;
        }
    }

    dsb();

    xil_printf("%s %s: checked=%u words, errors=%u\r\n",
               mode_names[mode],
               errors == 0U ? "PASS" : "FAIL",
               (unsigned int)words,
               (unsigned int)errors);

    return errors;
}

int main(void)
{
    const uintptr_t start = (uintptr_t)__ddr_test_start;
    const uintptr_t limit = (uintptr_t)__ddr_test_end;
    const uintptr_t program_end = (uintptr_t)end;

    uint32_t passed = 0U;
    uint32_t completed = 0U;
    uint32_t total_errors = 0U;

    xil_printf("\r\n=== DDR five-pattern test v1 ===\r\n");

    /* 防止链接配置意外变化后覆盖错误地址。 */
    if (start != 0x01000000U ||
        limit != 0x01100000U ||
        program_end > start) {
        xil_printf("ABORT: invalid or overlapping memory layout.\r\n");
        while (1) {}
    }

    const uint32_t words =
        (uint32_t)((limit - start) / sizeof(uint32_t));

    xil_printf("Start=0x%08x, end-exclusive=0x%08x\r\n",
               (unsigned int)start,
               (unsigned int)limit);

    xil_printf("Bytes=%u, words per mode=%u\r\n",
               (unsigned int)(limit - start),
               (unsigned int)words);

    xil_printf("Program end=0x%08x\r\n",
               (unsigned int)program_end);

    /*
     * 前提：单核、非AMP测试环境；
     * 核1不运行依赖共享L2的业务，DMA等不访问测试区。
     */
    Xil_DCacheFlush();
    Xil_DCacheDisable();
    dsb();

    xil_printf("Data cache disabled; destructive test begins.\r\n");

    for (uint32_t mode = 0U; mode < MODE_COUNT; mode++) {
        const uint32_t errors = test_mode(mode, start, words);

        completed++;
        total_errors += errors;

        if (errors != 0U) {
            xil_printf("Stopped after failure; remaining modes skipped.\r\n");
            break;
        }

        passed++;
    }

    xil_printf("\r\n=== SUMMARY ===\r\n");
    xil_printf("Completed=%u/%u, passed=%u, errors=%u\r\n",
               (unsigned int)completed,
               (unsigned int)MODE_COUNT,
               (unsigned int)passed,
               (unsigned int)total_errors);

    xil_printf("DDR TEST %s\r\n",
               passed == MODE_COUNT ? "PASS" : "FAIL");

    /* 不自动重测，不恢复缓存，不返回其他业务。 */
    while (1) {}

    return 0;
}
