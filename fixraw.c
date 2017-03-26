#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <math.h>

/*
The purpose of this is to convert MTK's RAW image data into RAW TIFF so that it can be processed by dcraw (and tools that use it).
It assumes that bayer pattern starts with BG
*/

#define SWAP_UINT16(x) (((x) >> 8) | ((x) << 8))
#define SWAP_UINT32(x) (((x) >> 24) | (((x) & 0x00FF0000) >> 8) | (((x) & 0x0000FF00) << 8) | ((x) << 24))

#define MODE 0744
#define BUFSIZE 8192

void write_int_le(int fd, uint32_t data)
{
 uint32_t buff = SWAP_UINT32(htonl(data));
 write(fd, &buff, 4);
}

void write_short_le(int fd, unsigned short data)
{
 unsigned short buff = SWAP_UINT16(htons(data));
 write(fd, &buff, 2);
}

void write_tag(int fd, short tag, short type, int size, int offset_or_data)
{
 write_short_le(fd, tag);
 write_short_le(fd, type);
 write_int_le(fd, size);
 write_int_le(fd, offset_or_data);
}

int main(int argc, char **argv)
{
 int img_width = 3264, img_height = 2448, bits = 10, bias = 0;

 int arg_off = 0;
 
 while(++arg_off < argc)
 {
  if (!strcmp(argv[arg_off], "-w") && arg_off+1 < argc)
  img_width = atoi(argv[++arg_off]);
  else if (!strcmp(argv[arg_off], "-h") && arg_off+1 < argc)
  img_height = atoi(argv[++arg_off]);
  else if (!strcmp(argv[arg_off], "-b") && arg_off+1 < argc)
  bits = atoi(argv[++arg_off]);
  else if (!strcmp(argv[arg_off], "-u") && arg_off+1 < argc)
  bias = atoi(argv[++arg_off]);
  else
  break;
 }
 
 if (argc-arg_off < 2)
 {
  fprintf(stderr, "%s [-w WIDTH] [-h HEIGHT] [-b BPP] [-u VALUE_TO_SUBTRACT] INPUT OUTPUT\n", argv[0]);
  exit(1);
 }
 
 int num_directories = 1;
 short num_ifds = 10; //must be accurate
 
 int fd = open(argv[arg_off], O_RDONLY);
 
 int fhead = open(argv[arg_off+1], O_WRONLY | O_CREAT | O_TRUNC, MODE);
 int fdata = open(argv[arg_off+1], O_WRONLY | O_CREAT, MODE);
 
 //compute needed number of tags
 //8 header + 2 count entries + num_ifds*12 + 4 next ifd

 lseek(fdata, 8 + num_directories*(2 + num_ifds*12 + 4), SEEK_SET);
 
 write(fhead, "II", 2); //little endian
 write(fhead, "\x2A", 2);
 write_int_le(fhead, 8);

 //start of ifd header
 write_short_le(fhead, num_ifds);
 
 write_tag(fhead, 5, 3, 1, img_width);
 write_tag(fhead, 6, 3, 1, img_height);
 write_tag(fhead, 256, 3, 1, img_width);
 write_tag(fhead, 257, 3, 1, img_height);
 write_tag(fhead, 258, 3, 1, bits); //bpp?
 
 //we set the manufacturer to "Minolta" just to get the proper load_raw function
 char *setmake = "Minolta";
 write_tag(fhead, 271, 2, strlen(setmake)+1, lseek(fdata, 0, SEEK_CUR));
 write(fdata, setmake, strlen(setmake)+1);
 
 //we want to set correct cfa...
 unsigned char cfa_pat[16] = {2,1,1,0, 2,1,1,0, 2,1,1,0, 2,1,1,0};
 write_tag(fhead, 9, 3, 1, 0); //filters=0
 write_tag(fhead, 64777, 1, 16, lseek(fdata, 0, SEEK_CUR));
 write(fdata, &cfa_pat, 16);
 
 write_tag(fhead, 273, 4, 1, lseek(fdata, 0, SEEK_CUR)); //bpp?
 
 unsigned char buff[8192];
 int tmp;

 while((tmp=read(fd, &buff, sizeof(buff))) > 0)
 {
  //noise is 161616, denoise it
  for(int t=0;t<tmp;t+=2)
  {  
   int v = (buff[t+1]<<8) | buff[t];

   v -= bias;
   
   if (v<0)
   v=0;
   
   buff[t] = v&0xff;
   buff[t+1] = v>>8;
  }
  write(fdata, &buff, tmp);
 }

 
 //after directory
 write_int_le(fhead, 0);
 
 return 0;
}