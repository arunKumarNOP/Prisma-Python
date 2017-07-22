# Reverse engineering Prisma API from Android App

There has been work to reverse engineer Prisma Application but only to break the SSL pinning and so we wanted to go a step further and along with removing SSL pinning, code a script to process images from desktop and maybe process multiple images at once.

<b>This project is not a replacement of Prisma application, it was done just our of curiosity to understand Prisma API better.</b>

Prisma version used : v2.5.3.178

### Bypassing SSL Pinning
To analyse the API calls made we need to intercept the traffic, we used BurpSuite. Without the interceptor in place we were able to use the application just fine but as soon as we introduced Burp the app just refused to connect to it's server.

We were able to see only one useful request to https://api.neuralprisma.com/config.

We already have the APK, we used [ApkStudio](https://github.com/vaibhavpandeyvpz/apkstudio) to disassamble the apk to smali, you can use the barebone apktool also.

We now know that its making requests to \<something\>prisma.com and we used that as a starting point and with a simple grep we were able to find our target method.

All juicy things will be in the package 'com.prisma' only so we change our directory to that first to limit our scope.

```bash
$ cd com.neuralprisma/smali/com/prisma
$ grep -r prisma.com
l/g/f.smali:    const-string v1, "api4.neuralprisma.com"
```
Analysing 'f' class in [jadx](https://github.com/skylot/jadx)

```java
package com.prisma.l.g;

import e.g;
import e.g.a;

public class f
{
    private g b() 
    {
        return new a().a("api4.neuralprisma.com", "sha1/yJUTaAGXKAosVcP805D1OgU7yfs=").a();
    }

    ....
}
```
I already have used retrofit and OkHttp3 library so quickly understood that its the pinning method.

```java
CertificatePinner certificatePinner()
{
   return new Builder().add(“api.example.com”, “sha1/XXXXXXXXXXXXXXX=”).build();
}
```

A quick google about implementing SSL Pinning and this obfuscated method becomes

```java
private CertificatePinner b()
{
   return new Builder().add(“api4.neuralprisma.com”, “sha1/yJUTaAGXKAosVcP805D1OgU7yfs=”).build();
}
```

we can easily remove the CertificatePinning by removing patching this method to

```java
private CertificatePinner b()
{
   return new Builder().build();
}
```

Lets switch to smali and remove those instructions

```java
.method private b()Le/g;
    .locals 5

    new-instance v0, Le/g$a;

    invoke-direct {v0}, Le/g$a;-><init>()V

    const-string v1, "api4.neuralprisma.com"

    const/4 v2, 0x1

    new-array v2, v2, [Ljava/lang/String;

    const/4 v3, 0x0

    const-string v4, "sha1/yJUTaAGXKAosVcP805D1OgU7yfs="

    aput-object v4, v2, v3

    invoke-virtual {v0, v1, v2}, Le/g$a;->a(Ljava/lang/String;[Ljava/lang/String;)Le/g$a;

    move-result-object v0

    invoke-virtual {v0}, Le/g$a;->a()Le/g;

    move-result-object v0

    return-object v0
.end method
```

to 

```java
.method private b()Le/g;
    .locals 5

    new-instance v0, Le/g$a;

    invoke-direct {v0}, Le/g$a;-><init>()V

    invoke-virtual {v0}, Le/g$a;->a()Le/g;

    move-result-object v0

    return-object v0
.end method
```

Save the file, compile, resign with your keys (its very easy to do in ApkStudio thats why i use it) and install it.

Now we can see requests made by the application, so SSL Pinning bypassed!!

### Disecting API

Playing with the app and with Burp doing its job we see this request which uploads our image, well there are few requests which make our job easier.

```
POST /upload/image HTTP/1.1
User-Agent: Prisma (178; My Phone - 6.0.0 - API 23 - 768x1280; Android 6.0; pie unknown)
prisma-image-sign: 5Eam/82ZNsQUYsGUSjDtUM3nNdtfxG531jUrjTS1G8A=
Content-Type: image/jpeg
Host: api4.neuralprisma.com
```

This contains this 'prisma-image-sign' which is kind of hash of image of some kind hash as changing it or removing it causes 403 error, we must figure out how its generated to use the API.

```bash
$ grep -r "prisma-image-sign"
styles/a/d.smali:            a = "prisma-image-sign"
```
Opening class 'd' in jadx.

```java
public interface d {
    @o(a = "/styles")
    b<com.prisma.styles.a.a.d> a(@a c cVar);

    @o(a = "/upload/image")
    b<e> a(@a ab abVar, @i(a = "prisma-image-sign") String str);
}
```
```bash
$ grep -r "com/prisma/styles/a/d;->a" 
 styles/z.smali:    invoke-interface {v0, v1}, Lcom/prisma/styles/a/d;-a(Lcom/prisma/styles/a/a/c;)Lg/b;
 styles/a/j.smali:    invoke-interface {v3, v2, v0}, Lcom/prisma/styles/a/d;-a(Le/ab;Ljava/lang/String;)Lg/b;
 store/d$6.smali:    invoke-interface {v0, v1}, Lcom/prisma/styles/a/d;-a(Lcom/prisma/styles/a/a/c;)Lg/b;
```

Examining them one by one we found <b>styles/a/j</b> as the interesting class and method <b>a(byte[] bArr)</b> was the method responsible for returning the hash.

```java
package com.prisma.styles.a;

private String a(byte[] bArr) {
    if (bArr.length >= 82) {
        bArr = a.a(Arrays.copyOfRange(bArr, 0, 42), Arrays.copyOfRange(bArr, bArr.length - 42, bArr.length));
    }
    String str = "";
    try {
        str = Base64.encodeToString(com.prisma.u.a.a(bArr, "duGB^Vy3Q&FQrJz2guKJBxNH3dAr/sQx"), 0).trim();
    } catch (Throwable e) {
        i.a.a.b(e, "Error encoding image", new Object[0]);
    }
    return str;
}
```

<b>com.prisma.u.a.a</b> is the method actually resposible for calculating the hash.

```java
public static byte[] a(byte[] bArr, String str) throws Exception {
    Mac instance = Mac.getInstance("HmacSHA256");
    instance.init(new SecretKeySpec(a(PrismaApplication.a().getString(R.string.settings_promo_code)).getBytes("UTF-8"), "HmacSHA256"));
    return instance.doFinal(bArr);
}
```

Well it turns out that the hashing function doesn't use the secret "duGB^Vy3Q&FQrJz2guKJBxNH3dAr/sQx" which is passed in second parameter, mistake or deception, who cares.

Calculating secret turns out to be MD5 hexdigest of R.string.settings_promo_code string - 'Add promo code', and then base64 of that digest.

In python.
```python
def getSecret():
    m = hashlib.md5()
    m.update('Add promo code')
    return m.hexdigest().encode('base64').strip()
```

Well now we can upload our image, the response is something like this

```json
{"status":"ok","id":"45396ad8-211b-4138-a7e2-bd4d2d44a99b_us","upload_status":"received","api_base_url":"https://api4.neuralprisma.com"}
```

"id" is used in further API calls along with style to apply to the image, which returns the modified image.

```
GET /process_direct/45396ad8-211b-4138-a7e2-bd4d2d44a99b_us/s_line?mode=freeaspect HTTP/1.1
User-Agent: Prisma (178; My Phone - 6.0.0 - API 23 - 768x1280; Android 6.0; pie unknown)
prisma-device-id: 7593facedeadb33f
Host: api4.neuralprisma.com
```

Here "<b>s_line</b>" is the style name, the whole list can be retrived using another API call, look in python script how thats retrieved.

The above API call returns the modified image.

### Prerequisite
To run the python script you need few things installed.

Python2.7	- https://www.python.org/download/releases/2.7/<br>
requests module - https://github.com/requests/requests

You can also install requests using pip

<pre>
pip install requests
</pre>

### Disclaimer
This is for education purposes for someone who wish to learn how to bypass SSL Pinning and to understand how to analyse app's requests. I should not be held responsible for misusage of the script or damage caused because of it. Use it at your own risk.

### Authors
Arun Kumar Shreevastava<br>
Sarbajit Saha