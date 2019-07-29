#if __cplusplus != 201103L
#error Please use C++11
#endif
#include <stdio.h>

int main() {
	int a, b; scanf("%d%d", &a, &b);
	printf("%d\n", a+b);
	return 0;
} 
