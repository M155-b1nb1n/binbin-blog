---
title: "日常练习-Web"
date: 2026-04-17 00:00:00
updated: 2026-04-19 01:27:28
description: "Web1.EZPHP（PCTF）创建容器打开网页后只有一句话：Please pass in “number” value the number value between 111111 and 999999:打开Burp suite进行抓包，发送到Intruder，改一下请求行，原始请求是 GET /，必须改成 GET /?number=§123456§，再"
tags:
  - "练习"
---
<h1 id="Web"><a href="#Web" class="headerlink" title="Web"></a>Web</h1><h2 id="1-EZPHP（PCTF）"><a href="#1-EZPHP%EF%BC%88PCTF%EF%BC%89" class="headerlink" title="1.EZPHP（PCTF）"></a>1.EZPHP（PCTF）</h2><p>创建容器打开网页后只有一句话：Please pass in “number” value the number value between 111111 and 999999:<br>打开Burp suite进行抓包，发送到Intruder，改一下请求行，原始请求是 GET /，必须改成 GET /?number=§123456§，再改payload类型为数值，范围从111111到999999，整数最大位为6。开始攻击后，将结果按响应长度（Length）排序，其中在payload=114514时，Length为3399。<br><img src="/binbin-blog/img/jgpctf.png" alt="结果"></p>
