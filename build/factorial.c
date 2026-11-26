#include <stdio.h>
#include <stdbool.h>
long fact(long n);
long fact(long n)
{
  if ((n <= 1))
  {
    return 1;
  }
  else
  ;
  return (n * fact((n - 1)));
}
int main(void) {
  printf("%ld\n", (long)(fact(5)));
  return 0;
}
