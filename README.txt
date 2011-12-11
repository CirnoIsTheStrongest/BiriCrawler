BiriCrawler is python script created to batch download images from
imageboards such as http://danbooru.donmai.us and http://oreno.imouto.org.
Please be aware that this is my first ever coding project of any sort, so you can expect some bugs and
ignorant code. If you have any suggestions to make/questions to ask, feel free to msg me on git, jump on my irc
at irc://irc.rizon.net/BiriBiri or email me at James.Is@winnar.org.

Python 2.7.2 or above is required. The default save path is currently Windows dependent, enter your own
if you're running on any other platform.

Basic usage:

Start the crawler with path/to/crawler.py [tag] -l [limit of images per page] -b [imageboard to use*]
-p [pages to parse] -c [maximum parallel downloads]

*The choices of boorus are currently as follows:

danbooru = http://danbooru.donmai.us
konachan = http://konachan.com
oreno = http://oreno.imouto.org
neko = http://nekobooru.net
sankaku = http://chan.sankakucomplex.com


Maximum connection value is 8, default is 4. Maximum images per page for each booru is generally 1000.


Example: C:\Users\Cirno\Downloads\crawler.py cirno -l 50 -b oreno -p 5 -c 6

This would download the Cirno tag, from oreno.imouto.org with a limit of 50 images per page, for 5 pages,
with 6 concurrent downloads. Note: While I have not hard-coded any limitations, please to not abuse
any of the above websites with this script. They offer a free service and deserve a bit of respect.
