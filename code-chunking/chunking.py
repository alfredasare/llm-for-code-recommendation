from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from typing import Type, List
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
import tiktoken

# sample vulnerable code
code_before = """
static MagickBooleanType WritePNMImage(const ImageInfo *image_info,Image *image,
  ExceptionInfo *exception)
{
  char
    buffer[MagickPathExtent],
    format,
    magick[MagickPathExtent];

  const char
    *value;

  MagickBooleanType
    status;

  MagickOffsetType
    scene;

  Quantum
    index;

  QuantumAny
    pixel;

  QuantumInfo
    *quantum_info;

  QuantumType
    quantum_type;

  register unsigned char
    *q;

  size_t
    extent,
    imageListLength,
    packet_size;

  ssize_t
    count,
    y;

  /*
    Open output image file.
  */
  assert(image_info != (const ImageInfo *) NULL);
  assert(image_info->signature == MagickCoreSignature);
  assert(image != (Image *) NULL);
  assert(image->signature == MagickCoreSignature);
  if (image->debug != MagickFalse)
    (void) LogMagickEvent(TraceEvent,GetMagickModule(),"%s",image->filename);
  assert(exception != (ExceptionInfo *) NULL);
  assert(exception->signature == MagickCoreSignature);
  status=OpenBlob(image_info,image,WriteBinaryBlobMode,exception);
  if (status == MagickFalse)
    return(status);
  scene=0;
  imageListLength=GetImageListLength(image);
  do
  {
    QuantumAny
      max_value;

    /*
      Write PNM file header.
    */
    packet_size=3;
    quantum_type=RGBQuantum;
    (void) CopyMagickString(magick,image_info->magick,MagickPathExtent);
    max_value=GetQuantumRange(image->depth);
    switch (magick[1])
    {
      case 'A':
      case 'a':
      {
        format='7';
        break;
      }
      case 'B':
      case 'b':
      {
        format='4';
        if (image_info->compression == NoCompression)
          format='1';
        break;
      }
      case 'F':
      case 'f':
      {
        format='F';
        if (SetImageGray(image,exception) != MagickFalse)
          format='f';
        break;
      }
      case 'G':
      case 'g':
      {
        format='5';
        if (image_info->compression == NoCompression)
          format='2';
        break;
      }
      case 'N':
      case 'n':
      {
        if ((image_info->type != TrueColorType) &&
            (SetImageGray(image,exception) != MagickFalse))
          {
            format='5';
            if (image_info->compression == NoCompression)
              format='2';
            if (SetImageMonochrome(image,exception) != MagickFalse)
              {
                format='4';
                if (image_info->compression == NoCompression)
                  format='1';
              }
            break;
          }
      }
      default:
      {
        format='6';
        if (image_info->compression == NoCompression)
          format='3';
        break;
      }
    }
    (void) FormatLocaleString(buffer,MagickPathExtent,"P%c\n",format);
    (void) WriteBlobString(image,buffer);
    value=GetImageProperty(image,"comment",exception);
    if (value != (const char *) NULL)
      {
        register const char
          *p;

        /*
          Write comments to file.
        */
        (void) WriteBlobByte(image,'#');
        for (p=value; *p != '\0'; p++)
        {
          (void) WriteBlobByte(image,(unsigned char) *p);
          if ((*p == '\n') || (*p == '\r'))
            (void) WriteBlobByte(image,'#');
        }
        (void) WriteBlobByte(image,'\n');
      }
    if (format != '7')
      {
        (void) FormatLocaleString(buffer,MagickPathExtent,"%.20g %.20g\n",
          (double) image->columns,(double) image->rows);
        (void) WriteBlobString(image,buffer);
      }
    else
      {
        char
          type[MagickPathExtent];

        /*
          PAM header.
        */
        (void) FormatLocaleString(buffer,MagickPathExtent,
          "WIDTH %.20g\nHEIGHT %.20g\n",(double) image->columns,(double)
          image->rows);
        (void) WriteBlobString(image,buffer);
        quantum_type=GetQuantumType(image,exception);
        switch (quantum_type)
        {
          case CMYKQuantum:
          case CMYKAQuantum:
          {
            packet_size=4;
            (void) CopyMagickString(type,"CMYK",MagickPathExtent);
            break;
          }
          case GrayQuantum:
          case GrayAlphaQuantum:
          {
            packet_size=1;
            (void) CopyMagickString(type,"GRAYSCALE",MagickPathExtent);
            if (IdentifyImageMonochrome(image,exception) != MagickFalse)
              (void) CopyMagickString(type,"BLACKANDWHITE",MagickPathExtent);
            break;
          }
          default:
          {
            quantum_type=RGBQuantum;
            if (image->alpha_trait != UndefinedPixelTrait)
              quantum_type=RGBAQuantum;
            packet_size=3;
            (void) CopyMagickString(type,"RGB",MagickPathExtent);
            break;
          }
        }
        if (image->alpha_trait != UndefinedPixelTrait)
          {
            packet_size++;
            (void) ConcatenateMagickString(type,"_ALPHA",MagickPathExtent);
          }
        if (image->depth > 32)
          image->depth=32;
        (void) FormatLocaleString(buffer,MagickPathExtent,
          "DEPTH %.20g\nMAXVAL %.20g\n",(double) packet_size,(double)
          ((MagickOffsetType) GetQuantumRange(image->depth)));
        (void) WriteBlobString(image,buffer);
        (void) FormatLocaleString(buffer,MagickPathExtent,
          "TUPLTYPE %s\nENDHDR\n",type);
        (void) WriteBlobString(image,buffer);
      }
    /*
      Convert runextent encoded to PNM raster pixels.
    */
    switch (format)
    {
      case '1':
      {
        unsigned char
          pixels[2048];

        /*
          Convert image to a PBM image.
        */
        (void) SetImageType(image,BilevelType,exception);
        q=pixels;
        for (y=0; y < (ssize_t) image->rows; y++)
        {
          register const Quantum
            *magick_restrict p;

          register ssize_t
            x;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          for (x=0; x < (ssize_t) image->columns; x++)
           {
             *q++=(unsigned char) (GetPixelLuma(image,p) >= (QuantumRange/2.0) ?
               '0' : '1');
            *q++=' ';
             if ((q-pixels+1) >= (ssize_t) sizeof(pixels))
               {
                 *q++='\n';
                 (void) WriteBlob(image,q-pixels,pixels);
                 q=pixels;
               }
             p+=GetPixelChannels(image);
           }
           *q++='\n';
          (void) WriteBlob(image,q-pixels,pixels);
          q=pixels;
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        if (q != pixels)
          {
            *q++='\n';
            (void) WriteBlob(image,q-pixels,pixels);
          }
        break;
      }
      case '2':
      {
        unsigned char
          pixels[2048];

        /*
          Convert image to a PGM image.
        */
        if (image->depth <= 8)
          (void) WriteBlobString(image,"255\n");
        else
          if (image->depth <= 16)
            (void) WriteBlobString(image,"65535\n");
          else
            (void) WriteBlobString(image,"4294967295\n");
        q=pixels;
        for (y=0; y < (ssize_t) image->rows; y++)
        {
          register const Quantum
            *magick_restrict p;

          register ssize_t
            x;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          for (x=0; x < (ssize_t) image->columns; x++)
          {
            index=ClampToQuantum(GetPixelLuma(image,p));
            if (image->depth <= 8)
              count=(ssize_t) FormatLocaleString(buffer,MagickPathExtent,"%u ",
                ScaleQuantumToChar(index));
            else
              if (image->depth <= 16)
                count=(ssize_t) FormatLocaleString(buffer,MagickPathExtent,
                  "%u ",ScaleQuantumToShort(index));
              else
                count=(ssize_t) FormatLocaleString(buffer,MagickPathExtent,
                  "%u ",ScaleQuantumToLong(index));
            extent=(size_t) count;
            if ((q-pixels+extent+1) >= sizeof(pixels))
              {
                *q++='\n';
                (void) WriteBlob(image,q-pixels,pixels);
                q=pixels;
              }
            (void) strncpy((char *) q,buffer,extent);
            q+=extent;
            p+=GetPixelChannels(image);
          }
          *q++='\n';
          (void) WriteBlob(image,q-pixels,pixels);
          q=pixels;
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        if (q != pixels)
          {
            *q++='\n';
            (void) WriteBlob(image,q-pixels,pixels);
          }
        break;
      }
      case '3':
      {
        unsigned char
          pixels[2048];

        /*
          Convert image to a PNM image.
        */
        (void) TransformImageColorspace(image,sRGBColorspace,exception);
        if (image->depth <= 8)
          (void) WriteBlobString(image,"255\n");
        else
          if (image->depth <= 16)
            (void) WriteBlobString(image,"65535\n");
          else
            (void) WriteBlobString(image,"4294967295\n");
        q=pixels;
        for (y=0; y < (ssize_t) image->rows; y++)
        {
          register const Quantum
            *magick_restrict p;

          register ssize_t
            x;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          for (x=0; x < (ssize_t) image->columns; x++)
          {
            if (image->depth <= 8)
              count=(ssize_t) FormatLocaleString(buffer,MagickPathExtent,
                "%u %u %u ",ScaleQuantumToChar(GetPixelRed(image,p)),
                ScaleQuantumToChar(GetPixelGreen(image,p)),
                ScaleQuantumToChar(GetPixelBlue(image,p)));
            else
              if (image->depth <= 16)
                count=(ssize_t) FormatLocaleString(buffer,MagickPathExtent,
                  "%u %u %u ",ScaleQuantumToShort(GetPixelRed(image,p)),
                  ScaleQuantumToShort(GetPixelGreen(image,p)),
                  ScaleQuantumToShort(GetPixelBlue(image,p)));
              else
                count=(ssize_t) FormatLocaleString(buffer,MagickPathExtent,
                  "%u %u %u ",ScaleQuantumToLong(GetPixelRed(image,p)),
                  ScaleQuantumToLong(GetPixelGreen(image,p)),
                  ScaleQuantumToLong(GetPixelBlue(image,p)));
            extent=(size_t) count;
            if ((q-pixels+extent+2) >= sizeof(pixels))
              {
                *q++='\n';
                (void) WriteBlob(image,q-pixels,pixels);
                q=pixels;
              }
            (void) strncpy((char *) q,buffer,extent);
            q+=extent;
            p+=GetPixelChannels(image);
          }
          *q++='\n';
          (void) WriteBlob(image,q-pixels,pixels);
          q=pixels;
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        if (q != pixels)
          {
            *q++='\n';
            (void) WriteBlob(image,q-pixels,pixels);
          }
        break;
      }
      case '4':
      {
        register unsigned char
          *pixels;

        /*
          Convert image to a PBM image.
        */
        (void) SetImageType(image,BilevelType,exception);
        image->depth=1;
        quantum_info=AcquireQuantumInfo(image_info,image);
        if (quantum_info == (QuantumInfo *) NULL)
          ThrowWriterException(ResourceLimitError,"MemoryAllocationFailed");
        (void) SetQuantumEndian(image,quantum_info,MSBEndian);
        quantum_info->min_is_white=MagickTrue;
        pixels=GetQuantumPixels(quantum_info);
        for (y=0; y < (ssize_t) image->rows; y++)
        {
          register const Quantum
            *magick_restrict p;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          extent=ExportQuantumPixels(image,(CacheView *) NULL,quantum_info,
            GrayQuantum,pixels,exception);
          count=WriteBlob(image,extent,pixels);
          if (count != (ssize_t) extent)
            break;
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        quantum_info=DestroyQuantumInfo(quantum_info);
        break;
      }
      case '5':
      {
        register unsigned char
          *pixels;

        /*
          Convert image to a PGM image.
        */
        if (image->depth > 32)
          image->depth=32;
        (void) FormatLocaleString(buffer,MagickPathExtent,"%.20g\n",(double)
          ((MagickOffsetType) GetQuantumRange(image->depth)));
        (void) WriteBlobString(image,buffer);
        quantum_info=AcquireQuantumInfo(image_info,image);
        if (quantum_info == (QuantumInfo *) NULL)
          ThrowWriterException(ResourceLimitError,"MemoryAllocationFailed");
        (void) SetQuantumEndian(image,quantum_info,MSBEndian);
        quantum_info->min_is_white=MagickTrue;
        pixels=GetQuantumPixels(quantum_info);
        extent=GetQuantumExtent(image,quantum_info,GrayQuantum);
        for (y=0; y < (ssize_t) image->rows; y++)
        {
          register const Quantum
            *magick_restrict p;

          register ssize_t
            x;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          q=pixels;
          switch (image->depth)
          {
            case 8:
            case 16:
            case 32:
            {
              extent=ExportQuantumPixels(image,(CacheView *) NULL,quantum_info,
                GrayQuantum,pixels,exception);
              break;
            }
            default:
            {
              if (image->depth <= 8)
                {
                  for (x=0; x < (ssize_t) image->columns; x++)
                  {
                    if (IsPixelGray(image,p) == MagickFalse)
                      pixel=ScaleQuantumToAny(ClampToQuantum(GetPixelLuma(
                        image,p)),max_value);
                    else
                      {
                        if (image->depth == 8)
                          pixel=ScaleQuantumToChar(GetPixelRed(image,p));
                        else
                          pixel=ScaleQuantumToAny(GetPixelRed(image,p),
                            max_value);
                      }
                    q=PopCharPixel((unsigned char) pixel,q);
                    p+=GetPixelChannels(image);
                  }
                  extent=(size_t) (q-pixels);
                  break;
                }
              if (image->depth <= 16)
                {
                  for (x=0; x < (ssize_t) image->columns; x++)
                  {
                    if (IsPixelGray(image,p) == MagickFalse)
                      pixel=ScaleQuantumToAny(ClampToQuantum(GetPixelLuma(image,
                        p)),max_value);
                    else
                      {
                        if (image->depth == 16)
                          pixel=ScaleQuantumToShort(GetPixelRed(image,p));
                        else
                          pixel=ScaleQuantumToAny(GetPixelRed(image,p),
                            max_value);
                      }
                    q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                    p+=GetPixelChannels(image);
                  }
                  extent=(size_t) (q-pixels);
                  break;
                }
              for (x=0; x < (ssize_t) image->columns; x++)
              {
                if (IsPixelGray(image,p) == MagickFalse)
                  pixel=ScaleQuantumToAny(ClampToQuantum(GetPixelLuma(image,p)),
                    max_value);
                else
                  {
                    if (image->depth == 16)
                      pixel=ScaleQuantumToLong(GetPixelRed(image,p));
                    else
                      pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                  }
                q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                p+=GetPixelChannels(image);
              }
              extent=(size_t) (q-pixels);
              break;
            }
          }
          count=WriteBlob(image,extent,pixels);
          if (count != (ssize_t) extent)
            break;
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        quantum_info=DestroyQuantumInfo(quantum_info);
        break;
      }
      case '6':
      {
        register unsigned char
          *pixels;

        /*
          Convert image to a PNM image.
        */
        (void) TransformImageColorspace(image,sRGBColorspace,exception);
        if (image->depth > 32)
          image->depth=32;
        (void) FormatLocaleString(buffer,MagickPathExtent,"%.20g\n",(double)
          ((MagickOffsetType) GetQuantumRange(image->depth)));
        (void) WriteBlobString(image,buffer);
        quantum_info=AcquireQuantumInfo(image_info,image);
        if (quantum_info == (QuantumInfo *) NULL)
          ThrowWriterException(ResourceLimitError,"MemoryAllocationFailed");
        (void) SetQuantumEndian(image,quantum_info,MSBEndian);
        pixels=GetQuantumPixels(quantum_info);
        extent=GetQuantumExtent(image,quantum_info,quantum_type);
        for (y=0; y < (ssize_t) image->rows; y++)
        {
          register const Quantum
            *magick_restrict p;

          register ssize_t
            x;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          q=pixels;
          switch (image->depth)
          {
            case 8:
            case 16:
            case 32:
            {
              extent=ExportQuantumPixels(image,(CacheView *) NULL,quantum_info,
                quantum_type,pixels,exception);
              break;
            }
            default:
            {
              if (image->depth <= 8)
                {
                  for (x=0; x < (ssize_t) image->columns; x++)
                  {
                    pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                    q=PopCharPixel((unsigned char) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelGreen(image,p),max_value);
                    q=PopCharPixel((unsigned char) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelBlue(image,p),max_value);
                    q=PopCharPixel((unsigned char) pixel,q);
                    p+=GetPixelChannels(image);
                  }
                  extent=(size_t) (q-pixels);
                  break;
                }
              if (image->depth <= 16)
                {
                  for (x=0; x < (ssize_t) image->columns; x++)
                  {
                    pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                    q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelGreen(image,p),max_value);
                    q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelBlue(image,p),max_value);
                    q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                    p+=GetPixelChannels(image);
                  }
                  extent=(size_t) (q-pixels);
                  break;
                }
              for (x=0; x < (ssize_t) image->columns; x++)
              {
                pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                pixel=ScaleQuantumToAny(GetPixelGreen(image,p),max_value);
                q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                pixel=ScaleQuantumToAny(GetPixelBlue(image,p),max_value);
                q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                p+=GetPixelChannels(image);
              }
              extent=(size_t) (q-pixels);
              break;
            }
          }
          count=WriteBlob(image,extent,pixels);
          if (count != (ssize_t) extent)
            break;
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        quantum_info=DestroyQuantumInfo(quantum_info);
        break;
      }
      case '7':
      {
        register unsigned char
          *pixels;

        /*
          Convert image to a PAM.
        */
        if (image->depth > 32)
          image->depth=32;
        quantum_info=AcquireQuantumInfo(image_info,image);
        if (quantum_info == (QuantumInfo *) NULL)
          ThrowWriterException(ResourceLimitError,"MemoryAllocationFailed");
        (void) SetQuantumEndian(image,quantum_info,MSBEndian);
        pixels=GetQuantumPixels(quantum_info);
        for (y=0; y < (ssize_t) image->rows; y++)
        {
          register const Quantum
            *magick_restrict p;

          register ssize_t
            x;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          q=pixels;
          switch (image->depth)
          {
            case 8:
            case 16:
            case 32:
            {
              extent=ExportQuantumPixels(image,(CacheView *) NULL,quantum_info,
                quantum_type,pixels,exception);
              break;
            }
            default:
            {
              switch (quantum_type)
              {
                case GrayQuantum:
                case GrayAlphaQuantum:
                {
                  if (image->depth <= 8)
                    {
                      for (x=0; x < (ssize_t) image->columns; x++)
                      {
                        pixel=ScaleQuantumToAny(ClampToQuantum(GetPixelLuma(
                          image,p)),max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        if (image->alpha_trait != UndefinedPixelTrait)
                          {
                            pixel=(unsigned char) ScaleQuantumToAny(
                              GetPixelAlpha(image,p),max_value);
                            q=PopCharPixel((unsigned char) pixel,q);
                          }
                        p+=GetPixelChannels(image);
                      }
                      break;
                    }
                  if (image->depth <= 16)
                    {
                      for (x=0; x < (ssize_t) image->columns; x++)
                      {
                        pixel=ScaleQuantumToAny(ClampToQuantum(GetPixelLuma(
                          image,p)),max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        if (image->alpha_trait != UndefinedPixelTrait)
                          {
                            pixel=(unsigned char) ScaleQuantumToAny(
                              GetPixelAlpha(image,p),max_value);
                            q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                          }
                        p+=GetPixelChannels(image);
                      }
                      break;
                    }
                  for (x=0; x < (ssize_t) image->columns; x++)
                  {
                    pixel=ScaleQuantumToAny(ClampToQuantum(GetPixelLuma(image,
                      p)),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    if (image->alpha_trait != UndefinedPixelTrait)
                      {
                        pixel=(unsigned char) ScaleQuantumToAny(
                          GetPixelAlpha(image,p),max_value);
                        q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                      }
                    p+=GetPixelChannels(image);
                  }
                  break;
                }
                case CMYKQuantum:
                case CMYKAQuantum:
                {
                  if (image->depth <= 8)
                    {
                      for (x=0; x < (ssize_t) image->columns; x++)
                      {
                        pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelGreen(image,p),
                          max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelBlue(image,p),
                          max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelBlack(image,p),
                          max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        if (image->alpha_trait != UndefinedPixelTrait)
                          {
                            pixel=ScaleQuantumToAny(GetPixelAlpha(image,p),
                              max_value);
                            q=PopCharPixel((unsigned char) pixel,q);
                          }
                        p+=GetPixelChannels(image);
                      }
                      break;
                    }
                  if (image->depth <= 16)
                    {
                      for (x=0; x < (ssize_t) image->columns; x++)
                      {
                        pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelGreen(image,p),
                          max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelBlue(image,p),
                          max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelBlack(image,p),
                          max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        if (image->alpha_trait != UndefinedPixelTrait)
                          {
                            pixel=ScaleQuantumToAny(GetPixelAlpha(image,p),
                              max_value);
                            q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                          }
                        p+=GetPixelChannels(image);
                      }
                      break;
                    }
                  for (x=0; x < (ssize_t) image->columns; x++)
                  {
                    pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelGreen(image,p),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelBlue(image,p),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelBlack(image,p),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    if (image->alpha_trait != UndefinedPixelTrait)
                      {
                        pixel=ScaleQuantumToAny(GetPixelAlpha(image,p),
                          max_value);
                        q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                      }
                    p+=GetPixelChannels(image);
                  }
                  break;
                }
                default:
                {
                  if (image->depth <= 8)
                    {
                      for (x=0; x < (ssize_t) image->columns; x++)
                      {
                        pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelGreen(image,p),
                          max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelBlue(image,p),
                          max_value);
                        q=PopCharPixel((unsigned char) pixel,q);
                        if (image->alpha_trait != UndefinedPixelTrait)
                          {
                            pixel=ScaleQuantumToAny(GetPixelAlpha(image,p),
                              max_value);
                            q=PopCharPixel((unsigned char) pixel,q);
                          }
                        p+=GetPixelChannels(image);
                      }
                      break;
                    }
                  if (image->depth <= 16)
                    {
                      for (x=0; x < (ssize_t) image->columns; x++)
                      {
                        pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelGreen(image,p),
                          max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        pixel=ScaleQuantumToAny(GetPixelBlue(image,p),
                          max_value);
                        q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                        if (image->alpha_trait != UndefinedPixelTrait)
                          {
                            pixel=ScaleQuantumToAny(GetPixelAlpha(image,p),
                              max_value);
                            q=PopShortPixel(MSBEndian,(unsigned short) pixel,q);
                          }
                        p+=GetPixelChannels(image);
                      }
                      break;
                    }
                  for (x=0; x < (ssize_t) image->columns; x++)
                  {
                    pixel=ScaleQuantumToAny(GetPixelRed(image,p),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelGreen(image,p),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    pixel=ScaleQuantumToAny(GetPixelBlue(image,p),max_value);
                    q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                    if (image->alpha_trait != UndefinedPixelTrait)
                      {
                        pixel=ScaleQuantumToAny(GetPixelAlpha(image,p),
                          max_value);
                        q=PopLongPixel(MSBEndian,(unsigned int) pixel,q);
                      }
                    p+=GetPixelChannels(image);
                  }
                  break;
                }
              }
              extent=(size_t) (q-pixels);
              break;
            }
          }
          count=WriteBlob(image,extent,pixels);
          if (count != (ssize_t) extent)
            break;
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        quantum_info=DestroyQuantumInfo(quantum_info);
        break;
      }
      case 'F':
      case 'f':
      {
        register unsigned char
          *pixels;

        (void) WriteBlobString(image,image->endian == LSBEndian ? "-1.0\n" :
          "1.0\n");
        image->depth=32;
        quantum_type=format == 'f' ? GrayQuantum : RGBQuantum;
        quantum_info=AcquireQuantumInfo(image_info,image);
        if (quantum_info == (QuantumInfo *) NULL)
          ThrowWriterException(ResourceLimitError,"MemoryAllocationFailed");
        status=SetQuantumFormat(image,quantum_info,FloatingPointQuantumFormat);
        if (status == MagickFalse)
          ThrowWriterException(ResourceLimitError,"MemoryAllocationFailed");
        pixels=GetQuantumPixels(quantum_info);
        for (y=(ssize_t) image->rows-1; y >= 0; y--)
        {
          register const Quantum
            *magick_restrict p;

          p=GetVirtualPixels(image,0,y,image->columns,1,exception);
          if (p == (const Quantum *) NULL)
            break;
          extent=ExportQuantumPixels(image,(CacheView *) NULL,quantum_info,
            quantum_type,pixels,exception);
          (void) WriteBlob(image,extent,pixels);
          if (image->previous == (Image *) NULL)
            {
              status=SetImageProgress(image,SaveImageTag,(MagickOffsetType) y,
                image->rows);
              if (status == MagickFalse)
                break;
            }
        }
        quantum_info=DestroyQuantumInfo(quantum_info);
        break;
      }
    }
    if (GetNextImageInList(image) == (Image *) NULL)
      break;
    image=SyncNextImageInList(image);
    status=SetImageProgress(image,SaveImagesTag,scene++,imageListLength);
    if (status == MagickFalse)
      break;
  } while (image_info->adjoin != MagickFalse);
  (void) CloseBlob(image);
  return(MagickTrue);
}
"""

# sample retrieved data
retrieved_data = """
Context:\nRetrieved metadata: {\'context\': \'CWE ID: CWE-119\', \'cwe\': \'CWE-119\', \'cwe_description\': \'The product performs operations on a memory buffer, but it can read from or write to a memory location that is outside of the intended boundary of the buffer.\', \'extended_cwe_description\': \'Certain languages allow direct addressing of memory locations and do not automatically ensure that these locations are valid for the memory buffer that is being referenced. This can cause read or write operations to be performed on memory locations that may be associated with other variables, data structures, or internal program data. As a result, an attacker may be able to execute arbitrary code, alter the intended control flow, read sensitive information, or cause the system to crash.\', \'name\': \'Improper Restriction of Operations within the Bounds of a Memory Buffer\', \'notes\': \'::TYPE:Applicable Platform:NOTE:It is possible in any programming languages without memory management support to attempt an operation outside of the bounds of a memory buffer, but the consequences will vary widely depending on the language, platform, and chip architecture.::\', \'potential_mitigations\': "::PHASE:Requirements:STRATEGY:Language Selection:DESCRIPTION:Use a language that does not allow this weakness to occur or provides constructs that make this weakness easier to avoid. For example, many languages that perform their own memory management, such as Java and Perl, are not subject to buffer overflows. Other languages, such as Ada and C#, typically provide overflow protection, but the protection can be disabled by the programmer. Be wary that a language\'s interface to native code may still be subject to overflows, even if the language itself is theoretically safe.::PHASE:Architecture and Design:STRATEGY:Libraries or Frameworks:DESCRIPTION:Use a vetted library or framework that does not allow this weakness to occur or provides constructs that make this weakness easier to avoid. Examples include the Safe C String Library (SafeStr) by Messier and Viega [REF-57], and the Strsafe.h library from Microsoft [REF-56]. These libraries provide safer versions of overflow-prone string-handling functions.::PHASE:Operation Build and Compilation:STRATEGY:Environment Hardening:DESCRIPTION:Use automatic buffer overflow detection mechanisms that are offered by certain compilers or compiler extensions. Examples include: the Microsoft Visual Studio /GS flag, Fedora/Red Hat FORTIFY_SOURCE GCC flag, StackGuard, and ProPolice, which provide various mechanisms including canary-based detection and range/index checking. D3-SFCV (Stack Frame Canary Validation) from D3FEND [REF-1334] discusses canary-based detection in detail.:EFFECTIVENESS:Defense in Depth::PHASE:Implementation:DESCRIPTION:Consider adhering to the following rules when allocating and managing an application\'s memory: Double check that the buffer is as large as specified. When using functions that accept a number of bytes to copy, such as strncpy(), be aware that if the destination buffer size is equal to the source buffer size, it may not NULL-terminate the string. Check buffer boundaries if accessing the buffer in a loop and make sure there is no danger of writing past the allocated space. If necessary, truncate all input strings to a reasonable length before passing them to the copy and concatenation functions.::PHASE:Operation Build and Compilation:STRATEGY:Environment Hardening:DESCRIPTION:Run or compile the software using features or extensions that randomly arrange the positions of a program\'s executable and libraries in memory. Because this makes the addresses unpredictable, it can prevent an attacker from reliably jumping to exploitable code. Examples include Address Space Layout Randomization (ASLR) [REF-58] [REF-60] and Position-Independent Executables (PIE) [REF-64]. Imported modules may be similarly realigned if their default memory addresses conflict with other modules, in a process known as rebasing (for Windows) and prelinking (for Linux) [REF-1332] using randomly generated addresses. ASLR for libraries cannot be used in conjunction with prelink since it would require relocating the libraries at run-time, defeating the whole purpose of prelinking. For more information on these techniques see D3-SAOR (Segment Address Offset Randomization) from D3FEND [REF-1335].:EFFECTIVENESS:Defense in Depth::PHASE:Operation:STRATEGY:Environment Hardening:DESCRIPTION:Use a CPU and operating system that offers Data Execution Protection (using hardware NX or XD bits) or the equivalent techniques that simulate this feature in software, such as PaX [REF-60] [REF-61]. These techniques ensure that any instruction executed is exclusively at a memory address that is part of the code segment. For more information on these techniques see D3-PSEP (Process Segment Execution Prevention) from D3FEND [REF-1336].:EFFECTIVENESS:Defense in Depth::PHASE:Implementation:DESCRIPTION:Replace unbounded copy functions with analogous functions that support length arguments, such as strcpy with strncpy. Create these if they are not available.:EFFECTIVENESS:Moderate::"}\n\nVulnerability: CVE-2012-3364\nWeakness: CWE-119\nRetrieved metadata: {\'Summary\': \'FreeRDP prior to version 2.0.0-rc4 contains a Heap-Based Buffer Overflow in function zgfx_decompress() that results in a memory corruption and probably even a remote code execution.\', \'context\': \'Vulnerability: CVE-2018-8785\\nWeakness: CWE-119\', \'cve\': \'CVE-2018-8785\', \'cwe\': \'CWE-119\', \'func_after\': \'static BOOL zgfx_compress_segment(ZGFX_CONTEXT* zgfx, wStream* s, const BYTE* pSrcData,\\n                                  UINT32 SrcSize, UINT32* pFlags)\\n{\\n\\t/* FIXME: Currently compression not implemented. Just copy the raw source */\\n\\tif (!Stream_EnsureRemainingCapacity(s, SrcSize + 1))\\n\\t{\\n\\t\\tWLog_ERR(TAG, "Stream_EnsureRemainingCapacity failed!");\\n\\t\\treturn FALSE;\\n\\t}\\n\\n\\t(*pFlags) |= ZGFX_PACKET_COMPR_TYPE_RDP8; /* RDP 8.0 compression format */\\n\\tStream_Write_UINT8(s, (*pFlags)); /* header (1 byte) */\\n\\tStream_Write(s, pSrcData, SrcSize);\\n\\treturn TRUE;\\n}\\n\', \'func_before\': \'static BOOL zgfx_compress_segment(ZGFX_CONTEXT* zgfx, wStream* s, const BYTE* pSrcData,\\n                                  UINT32 SrcSize, UINT32* pFlags)\\n{\\n\\t/* FIXME: Currently compression not implemented. Just copy the raw source */\\n\\tif (!Stream_EnsureRemainingCapacity(s, SrcSize + 1))\\n\\t{\\n\\t\\tWLog_ERR(TAG, "Stream_EnsureRemainingCapacity failed!");\\n\\t\\treturn FALSE;\\n\\t}\\n\\n\\t(*pFlags) |= ZGFX_PACKET_COMPR_TYPE_RDP8; /* RDP 8.0 compression format */\\n\\tStream_Write_UINT8(s, (*pFlags)); /* header (1 byte) */\\n\\tStream_Write(s, pSrcData, SrcSize);\\n\\treturn TRUE;\\n}\\n\'}\n
"""

def create_intelligent_chunks(code: str, retrieved_data: str, language: Language = Language.CPP) -> List[str]:
    """Create chunks with optimal size based on context window."""
    optimal_chunk_size = calculate_optimal_chunk_size(CONTEXT_WINDOW, retrieved_data)
    
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=language,
        chunk_size=optimal_chunk_size,
        chunk_overlap=int(optimal_chunk_size * 0.1)  # 10% overlap
    )
    docs = splitter.create_documents([code])
    return [doc.page_content for doc in docs]

def analyze_code_intelligently(code: str, retrieved_data: str) -> List[str]:
    """Main intelligent analysis function that decides between direct LLM and chunking."""
    print(f"Code length: {len(code)} characters")
    print(f"Estimated tokens: {count_tokens(code)}")
    
    if can_fit_in_context(code, retrieved_data):
        print("✅ Code fits in context window - using direct LLM analysis")
        result = direct_llm_analysis(code, retrieved_data)
        return [result]
    else:
        print("❌ Code exceeds context window - using agentic chunking approach")
        return agentic_chunking_analysis(code, retrieved_data)

def agentic_chunking_analysis(code: str, retrieved_data: str) -> List[str]:
    """Handle chunking analysis using agents."""
    code_chunks = create_intelligent_chunks(code, retrieved_data)
    print(f"Created {len(code_chunks)} chunks")
    
    output = []
    
    if len(code_chunks) == 1:
        extracted_code = agent_executor.invoke({"input": {
            "code": code_chunks[0],
            "retrieved_data": retrieved_data
        }})
        output.append(extracted_code['output'])
    else:
        # Multiple chunks - process each
        for i, chunk in enumerate(code_chunks):
            print(f"Processing chunk {i+1}/{len(code_chunks)}")
            extracted_code = agent_executor.invoke({"input": {
                "code": chunk,
                "retrieved_data": retrieved_data
            }})
            output.append(extracted_code['output'])
    
    return output


# Configuration
CONTEXT_WINDOW = 8192  # Configurable context window
MODEL_NAME = "gpt-4o-mini"
SAFETY_BUFFER = 500  # Reserve tokens for response

# Initialize LLM
llm = ChatOpenAI(model=MODEL_NAME)

# Initialize tiktoken encoder for the model
try:
    encoding = tiktoken.encoding_for_model(MODEL_NAME)
except KeyError:
    # Fallback to cl100k_base if model not found
    encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(encoding.encode(text))

def estimate_prompt_tokens(retrieved_data: str) -> int:
    """Estimate tokens used by the prompt template."""
    # Base prompt template tokens (estimated)
    base_prompt = """
    # CONTEXT #
    You are a software engineer and security expert who specializes in analyzing code snippets and finding vulnerabilities.

    # OBJECTIVE #
    Using the retrieved data to provide some context, extract only the relevant code that is affected by the CWE or CVE in question. If the snippet does not contain any vulnerabilities, 
    return the text "Not vulnerable" only.

    # STYLE #
    If you find any vulnerable snippet, return just that snippet as your response. If the snippet is not vulnerable, return the text "Not vulnerable".

    # TONE #
    Professional and technical.

    # AUDIENCE #
    Software engineers and security experts.

    # RESPONSE FORMAT #
    If the snippet has vulnerable code, present your response like this:
    ** Vulnerable Code: **
    Snippet of vulnerable code

    If the snippet is not vulnerable, respond strictly with: "Not vulnerable"

    
    Using this code snippet and the provided data which contains previous examples of this vulnerability, identify and extract the vulnerable code:
    # RETRIEVED DATA #
    {retrieved_data}
    
    # CODE SNIPPET #
    {code}
    """
    
    prompt_tokens = count_tokens(base_prompt)
    retrieved_data_tokens = count_tokens(retrieved_data)
    
    return prompt_tokens + retrieved_data_tokens

def can_fit_in_context(code: str, retrieved_data: str, context_window: int = CONTEXT_WINDOW) -> bool:
    """Check if code + prompt can fit in context window."""
    code_tokens = count_tokens(code)
    prompt_tokens = estimate_prompt_tokens(retrieved_data)
    total_tokens = code_tokens + prompt_tokens + SAFETY_BUFFER
    
    return total_tokens <= context_window

def calculate_optimal_chunk_size(context_window: int, retrieved_data: str) -> int:
    """Calculate optimal chunk size based on context window and prompt size."""
    prompt_tokens = estimate_prompt_tokens(retrieved_data)
    available_tokens = context_window - prompt_tokens - SAFETY_BUFFER
    
    # Convert tokens back to approximate characters (assuming 3.5 chars per token)
    chunk_size_chars = int(available_tokens * 3.5)
    
    # Ensure minimum viable chunk size
    return max(chunk_size_chars, 500)

def direct_llm_analysis(code: str, retrieved_data: str) -> str:
    """Directly analyze code using LLM without chunking and generate recommendation."""
    prompt = f"""
    # CONTEXT #
    You are a software engineer and security expert who specializes in providing recommendations for fixing vulnerabilities affected by different CWEs and CVEs.

    # OBJECTIVE #
    Based on the provided code snippet and CWE/CVE data, generate a comprehensive recommendation for fixing any vulnerabilities found. If no vulnerabilities are found, explain why the code is secure.

    # STYLE #
    Write in a technical and concise manner, providing clear and actionable steps.

    # TONE #
    Professional and technical.

    # AUDIENCE #
    The target audience is software developers and security professionals who are looking to secure their code against known vulnerabilities.

    # RESPONSE FORMAT #
    Provide a structured recommendation in the following format:
    - Issue: [Brief description of the vulnerability or security assessment]
    - Recommendation: [Detailed steps to fix the vulnerability or confirmation of security]
    - Fix: [Code snippet demonstrating the fix, or explanation of why no fix is needed]

    # PROMPT #
    Analyze the following code snippet considering the CWE/CVE context and provide a comprehensive security recommendation:
    
    # CWE/CVE Data #
    {retrieved_data}

    # Code Snippet #
    {code}
    """
    
    response = llm.invoke(prompt.strip())
    return response.content if hasattr(response, 'content') else str(response)

# Pull prompt template
prompt = hub.pull("hwchase17/openai-tools-agent")

# Define Pydantic models for tool arguments
class ExtractVulnerableCodeArgs(BaseModel):
	code: str = Field(description="Code snippet to extract vulnerable code from", example=code_before)
	retrieved_data: str = Field(description="Retrieved data to provide context for the code snippet")
    
# Extract vulnerable code tool
class ExtractVulnerableCodeTool(BaseTool):
	name: str = "extract_vulnerable_snippet"
	description: str = "Extracts vulnerable code from a code snippet"
	args_schema: Type[BaseModel] = ExtractVulnerableCodeArgs
    
	def _run(self, code: str, retrieved_data: str) -> str:
		prompt = f"""
        # CONTEXT #
        You are a software engineer and security expert who specializes in analyzing code snippets and finding vulnerabilities.

        # OBJECTIVE #
        Using the retrieved data to provide some context, extract only the relevant code that is affected by the CWE or CVE in question. If the snippet does not contain any vulnerabilities, 
		return the text "Not vulnerable" only.

        # STYLE #
        If you find any vulnerable snippet, return just that snippet as your response. If the snippet is not vulnerable, return the text "Not vulnerable".

        # TONE #
        Professional and technical.

        # AUDIENCE #
        Software engineers and security experts.

        # RESPONSE FORMAT #
        If the snippet has vulnerable code, present your response like this:
		** Vulnerable Code: **
		Snippet of vulnerable code

		If the snippet is not vulnerable, respond strictly with: "Not vulnerable"

		
		Using this code snippet and the provided data which contains previous examples of this vulnerability, identify and extract the vulnerable code:
		# RETRIEVED DATA #
		{retrieved_data}
		
		# CODE SNIPPET #
		{code}
        """
		
		comparison = llm.invoke(prompt)
		return comparison


class GenerateFinalRecommendationArgs(BaseModel):
    chunk_outputs: List[str] = Field(description="Array of responses from the different code chunks")
    cwe_cve_data: str = Field(description="Information about the CWE/CVE vulnerability")

# Generate final recommendation tool
class GenerateFinalRecommendationTool(BaseTool):
    name: str = "generate_final_recommendation"
    description: str = "Generates a final recommendation for fixing the vulnerability based on the chunk outputs"
    args_schema: Type[BaseModel] = GenerateFinalRecommendationArgs
    
    def _run(self, chunk_outputs: List[str], cwe_cve_data: str) -> str:
        prompt = f"""
        # CONTEXT #
        You are a software engineer and security expert who specializes in providing recommendations for fixing vulnerabilities affected by different CWEs and CVEs.

        # OBJECTIVE #
        Based on the array of outputs from different code chunks and the provided CWE/CVE data, generate a recommendation for fixing the vulnerability. Ignore any output
        chunk that is marked as "Not vulnerable" or describes the chunk it received as not vulnerable.

        # STYLE #
        Write in a technical and concise manner, providing clear and actionable steps. 

        # TONE #
        Professional and technical.

        # AUDIENCE #
        The target audience is software developers and security professionals who are looking to secure their code against known vulnerabilities.

        # RESPONSE FORMAT #
        Provide a structured recommendation in the following format:
        - Issue: [Brief description of the vulnerability]
        - Recommendation: [Detailed steps to fix the vulnerability based on the CWE/CVE context and outputs]
        - Fix: [Code snippet demonstrating the fix]

        # PROMPT #
        Based on the following outputs from the analyzed code chunks, and considering the CWE/CVE context, provide a final recommendation for fixing the vulnerability:
        
        # CWE/CVE Data #
        {cwe_cve_data}

        # Chunk Outputs #
        {chunk_outputs}
        """
        
        recommendation = llm.invoke(prompt.strip())
        return recommendation

# Initialize the tool
tools = [
	ExtractVulnerableCodeTool()
]

# Create an agent executor
agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# Create the agent executor
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)


# Main execution with intelligent token-based approach
output = analyze_code_intelligently(code_before, retrieved_data)

print("\n=== ANALYSIS RESULTS ===")
for i, result in enumerate(output):
    if len(output) > 1:
        print(f"\nChunk {i+1} result:")
    print(result)


# Generate final recommendation if we have multiple outputs
if len(output) > 1:
    print("\n=== GENERATING FINAL RECOMMENDATION ===")
    
    final_tools = [GenerateFinalRecommendationTool()]
    
    final_agent = create_tool_calling_agent(
        llm=llm,
        tools=final_tools,
        prompt=prompt
    )
    
    final_agent_executor = AgentExecutor.from_agent_and_tools(
        agent=final_agent,
        tools=final_tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    final_recommendation = final_agent_executor.invoke({"input": {
        "chunk_outputs": output,
        "cwe_cve_data": retrieved_data
    }})
    
    print("\n=== FINAL RECOMMENDATION ===")
    print(final_recommendation['output'])
else:
    print("\n=== SINGLE OUTPUT - NO RECOMMENDATION SYNTHESIS NEEDED ===")