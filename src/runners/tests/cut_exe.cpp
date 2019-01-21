#include <cassert>
#include <cstdio>

#ifdef __unix__
#include <sys/stat.h>
#endif

int main(int argc, char **argv) {
  assert(argc == 3);
  FILE *inFile = fopen(argv[1], "rb");
  FILE *outFile = fopen(argv[2], "wb");
  char buf[32];
  int bytesRead = fread(buf, sizeof(char), 32, inFile);
  fwrite(buf, sizeof(char), bytesRead, outFile);
  fclose(inFile);
  fclose(outFile);
#ifdef __unix__
  chmod(argv[2], 0100755);
#endif
  return 0;
}
