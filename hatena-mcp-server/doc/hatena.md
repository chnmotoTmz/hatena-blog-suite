はてなブログAtomPub
本ドキュメントに関する注意事項
本ドキュメントははてなブログにおける Atom Publishing Protocol の仕様を解説するものです。

Atom Publishing Protocol とは
Atom Publishing Protocol(以下 AtomPub) はウェブリソースを公開、編集するためのアプリケーション・プロトコル仕様です。はてなブログのAtomPubと通じて、開発者ははてなブログのエントリを参照、投稿、編集、削除するようなオリジナルのアプリケーションを作成できます。

AtomPub について詳しくは http://www.ietf.org/rfc/rfc5023.txt (英語)などを参照してください。

URIの表記について
本仕様解説中に現れる URI は URI Template の記法に基づいて以下のように表記されます。

https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/{entry_id}
https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page/{page_id}

各変数の意味と書式は次のようになります。

はてなID
意味:あなたのはてなID
ブログID
意味:ブログのID
書式:ブログのドメイン (例: example.hatenablog.com)
ルートURL
意味:ブログのトップページのURL
書式:ブログのドメイン。サブディレクトリオプションを利用している場合はサブディレクトリも含む (例: example.hatenablog.com, example.com, example.com/subdirectory)
entry_id:
意味:ブログエントリのID
書式:epochを表す数値 (例: 1227232862) または、英数字文字列
page_id:
意味:固定ページのID
書式:epochを表す数値 (例: 1227232862) または、英数字文字列
有料プラン（はてなブログPro、はてなブログBusinessなど）の独自ドメイン機能をご利用の方は、独自ドメイン設定前のブログのドメインがブログのIDとなります。ブログの詳細設定のAtomPub項内のルートエンドポイントをご参照ください。

はてなブログにおける AtomPub 実装の概要
HTTP の GET/POST/PUT/DELETE を特定の URI に対してリクエストし、そのリクエストに規定の XML 文書を加えて送信することでインタフェースが用意している操作を行うことができます。

AtomPub では、基本的に記事の集合を表す「コレクション」と、個々の操作の対象記事にあたる「メンバ」があります。コレクションとメンバはそれぞれに URI を持ち、その URI に対して操作を行います。はてなブログにおける コレクションURI と メンバURI は以下のとおりです。URIはすべてhttpsになっておりますのでご注意ください。

コレクションURI（ブログエントリ）	https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry
メンバURI（ブログエントリ）	https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/{entry_id}
コレクションURI（固定ページ）	https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page
メンバURI（固定ページ）	https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page/{page_id}
どのようなコレクションが存在するかを記述するサービスに関しては、以下のURIを用いる事が出来ます。

サービス文書URI	https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom
また、はてなブログの AtomPub ではコレクションで利用されるカテゴリを記述する文書を以下の URI で提供しています。

カテゴリ文書URI	https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/category
一部の操作はそのレスポンスとして規定の XML 文書を返却します。

現時点で API がサポートしている操作は以下です。

固定ページは、有料プラン（はてなブログPro、はてなブログBusinessなど）に加入しているユーザーが運営するブログで利用できます。

ブログの操作 (コレクション)
ブログエントリ一覧の取得 (コレクションURI への GET)
ブログエントリの新規投稿 (コレクションURIへの POST)
固定ページ一覧の取得 (コレクションURI への GET)
固定ページの新規投稿 (コレクションURIへの POST)
ブログエントリ・固定ページの操作 (メンバ)
ブログエントリの取得 (メンバURI の GET)
ブログエントリの更新 (メンバURI への PUT)
ブログエントリの削除 (メンバURI への DELETE)
固定ページの取得 (メンバURI の GET)
固定ページの更新 (メンバURI への PUT)
固定ページの削除 (メンバURI への DELETE)
サービスの操作 (サービス文書)
コレクション一覧の取得 (サービス文書URI の GET)
カテゴリの操作 (カテゴリ文書)
カテゴリ一覧の取得 (カテゴリ文書URI の GET)
以下、はてなブログ AtomPub の詳細を解説します。

認証
はてなブログAtomPub を利用するために、クライアントは OAuth 認証、WSSE認証、Basic認証のいずれかを行う必要があります。

OAuth認証の詳細に関しては、はてなのOAuthを利用する方法を参照してください。はてなブログAtomPub では、全操作に関して read_private 操作 及び write_private 操作の承認を得ている必要があります。

WSSE認証の詳細に関してははてなサービスにおける WSSE認証を御覧ください。

Basic認証についてはユーザ名としてはてなIDを、パスワードとしてAPIキーを利用することで認証できます。Basic認証はAPIのURLがhttpsではじまる場合にのみ利用できます。

本WSSE認証における、ユーザ名にははてなIDを、パスワードには、ブログの詳細設定に記載されたAPIキーをご利用下さい。

文字コード
はてなブログ AtomPub では文字コードとして UTF-8 を利用します。リクエストXML 、レスポンスXML 共に UTF-8 として扱ってください。

サービス文書
はてなブログ AtomPub で操作できるコレクションの一覧を含むサービス文書を取得できます。

固定ページに関するコレクションの一覧は、固定ページを利用可能なブログでのみ表示されます。

リクエスト
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom

レスポンス
HTTP/1.1 200 OK
Content-Type: application/atomsvc+xml; charset=utf-8

<?xml version="1.0" encoding="utf-8"?>
<service xmlns="http://www.w3.org/2007/app">
  <workspace>
    <atom:title xmlns:atom="http://www.w3.org/2005/Atom">ブログタイトル</atom:title>
    <collection href="https://blog.hatena.ne.jp/はてなID/ブログID/atom/entry">
      <atom:title xmlns:atom="http://www.w3.org/2005/Atom">記事一覧</atom:title>
      <accept>application/atom+xml;charset=utf-8;type=entry</accept>
    </collection>
    <collection href="https://blog.hatena.ne.jp/はてなID/ブログID/atom/page">
      <atom:title xmlns:atom="http://www.w3.org/2005/Atom">固定ページ一覧</atom:title>
      <accept>application/atom+xml;charset=utf-8;type=entry</accept>
    </collection>
  </workspace>
</service>

コレクション
はてなブログのエントリ・固定ページを操作するためのコレクションです。ブログエントリ・固定ページの一覧取得、新規投稿を行うことができます。

ブログエントリの一覧取得
コレクション URI を GET することで、ブログエントリ一覧を取得できます。一度に7件のブログエントリを取得できます。また、取得したブログエントリ一覧が、コレクションの部分的リストである場合には、 page パラメータを付与する事で、7件目以降のブログエントリも取得出来ます。続きについては、AtomPub の仕様に基づき、部分的リストの続きは rel=next となる atom:link の href 属性がその URI となります。page パラメータを付与しない場合には、最新の7件を取得します。

「寄稿者」権限のブログメンバーは、自身が作成した下書きのエントリのみ取得できます。

リクエスト
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry?page=1377575606

レスポンス
一覧取得のレスポンスは以下のようになります。ブログエントリの内容については、ブログエントリの取得の項目を参照してください。

<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:app="http://www.w3.org/2007/app">
  <link rel="first" href="https://blog.hatena.ne.jp/{はてなID}}/{ブログID}/atom/entry" />
  <link rel="next" href="https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry?page=1377584217" />
  <title>ブログタイトル</title>
  <link rel="alternate" href="http://{ルートURL}/"/>
  <updated>2013-08-27T15:17:06+09:00</updated>
  <author>
    <name>{はてなID}</name>
  </author>
  <generator uri="http://blog.hatena.ne.jp/" version="100000000">Hatena::Blog</generator>
  <id>hatenablog://blog/2000000000000</id>

  <entry>
    <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
    <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/
    ブログID}/atom/entry/2500000000"/>
    <link rel="alternate" type="text/html" href="http://{ルートURL}/entry/2013/09/02/112823"/>
    <author><name>{はてなID}</name></author>
    <title>記事タイトル</title>
    <updated>2013-09-02T11:28:23+09:00</updated>
    <published>2013-09-02T11:28:23+09:00</published>
    <app:edited>2013-09-02T11:28:23+09:00</app:edited>
    <summary type="text"> 記事本文 リスト1 リスト2 内容 </summary>
    <content type="text/x-hatena-syntax">
      ** 記事本文
      - リスト1
      - リスト2
      内容
    </content>
    <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
      <div class=&quot;section&quot;>
      <h4>記事本文</h4>
      <ul>
      <li>リスト1</li>
      <li>リスト2</li>
      </ul><p>内容</p>
      </div>
    </hatena:formatted-content>
    <app:control>
      <app:draft>no</app:draft>
      <app:preview>no</app:preview>
    </app:control>
  </entry>
  <entry>
  ...
  </entry>
  ...
</feed>

ブログエントリの投稿
コレクションURIに対して XML 文書を POST することで、ブログエントリを投稿できます。このブログエントリは、ブログに登録された記法で書かれたものであると解釈されます。

「寄稿者」権限のブログメンバーは、下書きエントリのみ投稿可能です。

以下の例ははてな記法で記述すると登録したブログにおける例です。

リクエスト
リクエストXML文書に必要なパラメータは以下です。

title要素 ブログエントリのタイトル
content要素 記述されたブログエントリの本文
updated要素 任意項目です。ブログエントリを投稿する日時を指定することができます。
category要素ブログ エントリのカテゴリを指定出来ます。(複数可)
term属性 カテゴリ名を指定します。
app:control/app:draft要素 ブログエントリを下書きにするか指定出来ます。"yes"を指定すると下書きになります。指定を行わなかった場合、下書きでないものとみなされます。
app:control/app:preview要素 ブログエントリが下書きのとき下書きプレビューの共有URLを発行するか指定できます。"yes"を指定すると共有URLが発行され、レスポンスのrel=previewであるatom:link要素のhref属性が共有URLとなります。指定を行わなかった場合、下書きプレビュー用の共有URLは発行されません。また、下書きではないエントリに対して"yes"を指定しても無効となります。
hatenablog:custom-url要素 ブログエントリのカスタムURLを指定できます。（省略可）
POST https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry

<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>エントリタイトル</title>
  <author><name>name</name></author>
  <content type="text/plain">
    ** エントリ本文
  </content>
  <updated>2008-01-01T00:00:00</updated>
  <category term="Scala" />
  <app:control>
    <app:draft>{yes | no}</app:draft>
    <app:preview>{yes | no}</app:preview>
  </app:control>
  <hatenablog:custom-url xmlns:hatenablog="http://www.hatena.ne.jp/info/xmlns#hatenablog">2008-happy-new-year</hatenablog:custom-url>
</entry>


レスポンス
レスポンスは正常時にHTTPステータス201を返します。 Locationヘッダに新しく作成したブログエントリのメンバURIが含まれます。 ブログエントリの内容については、ブログエントリの取得の項目を参照してください。

HTTP/1.1 201 Created
Content-Type: application/atom+xml;type=entry
Location: https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/{entry_id}

<?xml version="1.0" encoding="utf-8"?>
<entry>
  <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
  <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/2500000000"/>
  <link rel="alternate" type="text/html" href="http://{ルートURL}/entry/2008-happy-new-year"/>
  <author><name>{はてなID}</name></author>
  <title>記事タイトル</title>
  <updated>2013-09-02T11:28:23+09:00</updated>
  <published>2013-09-02T11:28:23+09:00</published>
  <app:edited>2013-09-02T11:28:23+09:00</app:edited>
  <summary type="text"> エントリ本文 </summary>
  <content type="text/x-hatena-syntax">
    ** エントリ本文
  </content>
  <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
    <div class=&quot;section&quot;>
    <h4>記事本文</h4>
  </hatena:formatted-content>
  <category term="Scala" />
   <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
<entry>

固定ページの一覧取得
コレクション URI を GET することで、ブログの固定ページ一覧を取得できます。一度に10件の固定ページを取得できます。また、取得した固定ページ一覧が、コレクションの部分的リストである場合には、 page パラメータを付与する事で、10件目以降の固定ページも取得出来ます。続きについては、AtomPub の仕様に基づき、部分的リストの続きは rel=next となる atom:link の href 属性がその URI となります。page パラメータを付与しない場合には、最新の10件を取得します。

「寄稿者」権限のブログメンバーは、自身が作成した下書きの固定ページのみ取得できます。

リクエスト
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page?page=1377575606

レスポンス
一覧取得のレスポンスは以下のようになります。固定ページの内容については、固定ページの取得の項目を参照してください。

<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:app="http://www.w3.org/2007/app">
  <link rel="first" href="https://blog.hatena.ne.jp/{はてなID}}/{ブログID}/atom/page" />
  <link rel="next" href="https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page?page=1377584217" />
  <title>ブログタイトル</title>
  <link rel="alternate" href="http://{ルートURL}/"/>
  <updated>2013-08-27T15:17:06+09:00</updated>
  <author>
    <name>{はてなID}</name>
  </author>
  <generator uri="http://blog.hatena.ne.jp/" version="100000000">Hatena::Blog</generator>
  <id>hatenablog://blog/2000000000000</id>

  <entry>
    <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
    <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/
    ブログID}/atom/page/2500000000"/>
    <link rel="alternate" type="text/html" href="http://{ルートURL}/page/2013/09/02/112823"/>
    <author><name>{はてなID}</name></author>
    <title>記事タイトル</title>
    <updated>2013-09-02T11:28:23+09:00</updated>
    <published>2013-09-02T11:28:23+09:00</published>
    <app:edited>2013-09-02T11:28:23+09:00</app:edited>
    <summary type="text"> 記事本文 リスト1 リスト2 内容 </summary>
    <content type="text/x-hatena-syntax">
      ** 記事本文
      - リスト1
      - リスト2
      内容
    </content>
    <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
      <div class=&quot;section&quot;>
      <h4>記事本文</h4>
      <ul>
      <li>リスト1</li>
      <li>リスト2</li>
      </ul><p>内容</p>
      </div>
    </hatena:formatted-content>
    <app:control>
      <app:draft>no</app:draft>
      <app:preview>no</app:preview>
    </app:control>
  </entry>
  <entry>
  ...
  </entry>
  ...
</feed>


固定ページの投稿
コレクションURIに対して XML 文書を POST することで、固定ページを投稿できます。この固定ページは、ブログに登録された記法で書かれたものであると解釈されます。

「寄稿者」権限のブログメンバーは、下書きの固定ページのみ投稿可能です。

固定ページのレイアウト設定をAPIから操作することはできません。APIを用いて新規に作成された固定ページのレイアウトは記事レイアウトになります。

以下の例ははてな記法で記述すると登録したブログにおける例です。

リクエスト
リクエストXML文書に必要なパラメータは以下です。

title要素 固定ページのタイトル
content要素 記述された固定ページの本文
updated要素 任意項目です。固定ページを投稿する日時を指定します。
app:control/app:draft要素 固定ページを下書きにするか指定出来ます。"yes"を指定すると下書きになります。指定を行わなかった場合、下書きでないものとみなされます。
app:control/app:preview要素 固定ページが下書きのとき下書きプレビューの共有URLを発行するか指定できます。"yes"を指定すると共有URLが発行され、レスポンスのrel=previewであるatom:link要素のhref属性が共有URLとなります。指定を行わなかった場合、下書きプレビュー用の共有URLは発行されません。また、下書きではない固定ページに対して"yes"を指定しても無効となります。
hatenablog:custom-url要素 固定ページのURLを指定します。なお、空文字は指定できません。
POST https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page

<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>エントリタイトル</title>
  <author><name>name</name></author>
  <content type="text/plain">
    ** エントリ本文
  </content>
  <updated>2008-01-01T00:00:00</updated>
  <category term="Scala" />
  <app:control>
    <app:draft>{yes | no}</app:draft>
    <app:preview>{yes | no}</app:preview>
  </app:control>
  <hatenablog:custom-url xmlns:hatenablog="http://www.hatena.ne.jp/info/xmlns#hatenablog">2008-happy-new-year</hatenablog:custom-url>
</entry>


レスポンス
レスポンスは正常時にHTTPステータス201を返します。 Locationヘッダに新しく作成した固定ページのメンバURIが含まれます。 固定ページの内容については、固定ページの取得の項目を参照してください。

HTTP/1.1 201 Created
Content-Type: application/atom+xml;type=entry
Location: https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page/{page_id}

<?xml version="1.0" encoding="utf-8"?>
<entry>
  <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
  <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/2500000000"/>
  <link rel="alternate" type="text/html" href="http://{ルートURL}/2008-happy-new-year"/>
  <author><name>{はてなID}</name></author>
  <title>記事タイトル</title>
  <updated>2013-09-02T11:28:23+09:00</updated>
  <published>2013-09-02T11:28:23+09:00</published>
  <app:edited>2013-09-02T11:28:23+09:00</app:edited>
  <summary type="text"> エントリ本文 </summary>
  <content type="text/x-hatena-syntax">
    ** エントリ本文
  </content>
  <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
    <div class=&quot;section&quot;>
    <h4>記事本文</h4>
  </hatena:formatted-content>
   <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
<entry>

メンバ
はてなブログのブログエントリ・固定ページを操作するためのメンバです。ブログエントリ・固定ページの取得、編集、削除を行うことができます。

ブログエントリの取得
メンバURIをGETすることで、ブログエントリを取得できます。

「寄稿者」権限のブログメンバーは自身が投稿した下書きエントリのみ取得可能です。

リクエスト
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/{entry_id}

レスポンス
レスポンスは正常時にHTTPステータス200を返します。
レスポンスXML文書はHatena XML名前空間によって拡張されています。
summaryは最大140文字の文書要約が記載されます。
contentにははてなブログに登録されたシンタックスと解釈されたオリジナルな文面が記載されます
type属性には以下の3つの値のいずれかが付与されます。
text/html 見たままモード
text/x-hatena-syntax はてな記法
text/x-markdown マークダウン記法
codoc連携記事を取得した場合、contentには記事の有料部分が含まれます。
hatena:formatted-contentには常にエンコードされたhtmlが返却されます。
<?xml version="1.0" encoding="utf-8"?>
<entry>
  <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
  <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/
  ブログID}/atom/entry/2500000000"/>
  <link rel="alternate" type="text/html" href="http://{ルートURL}/entry/2013/09/02/112823"/>
  <author><name>{はてなID}</name></author>
  <title>記事タイトル</title>
  <updated>2013-09-02T11:28:23+09:00</updated>
  <published>2013-09-02T11:28:23+09:00</published>
  <app:edited>2013-09-02T11:28:23+09:00</app:edited>
  <summary type="text"> 記事本文 リスト1 リスト2 内容 </summary>
  <content type="text/x-hatena-syntax">
    ** 記事本文
    - リスト1
    - リスト2
    内容
  </content>
  <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
    <div class=&quot;section&quot;>
    <h4>記事本文</h4>

    <ul>
    <li>リスト1</li>
    <li>リスト2</li>
    </ul><p>内容</p>
    </div>
  </hatena:formatted-content>
  <category term="Scala" />
  <category term="Perl" />
  <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
</entry>

ブログエントリの編集
メンバURIに対してXML文書をPUTすることで、ブログエントリを編集できます。ブログエントリの記法は編集前に適用されていたものと同じ記法が適用されます。

「寄稿者」権限のブログメンバーは自身が投稿した下書きエントリのみ編集可能です。

新規の有料販売記事の作成・投稿や、販売価格・サブスクリプションの設定など、記事本文の編集以外のcodoc連携機能は未対応のため、PCまたはスマートフォンのブラウザからご利用ください。

リクエスト
リクエストXML文書に必要なパラメータは以下です。

title要素 ブログエントリのタイトル
content要素 記述されたブログエントリの本文
updated要素 任意項目です。ブログエントリの投稿日時を指定することができます。
category要素 ブログエントリのカテゴリを指定出来ます。(複数可)
term属性 カテゴリ名を指定します。
app:control/app:draft要素 ブログエントリを下書きにするか指定出来ます。"yes"を指定すると下書きになります。指定を行わなかった場合、下書きでないものとみなされます。「寄稿者」権限のブログメンバーは下書きにする必要があります。
app:control/app:preview要素 ブログエントリが下書きのとき下書きプレビューの共有URLを発行するか指定できます。"yes"を指定すると共有URLが発行され、レスポンスのrel=previewであるatom:link要素のhref属性が共有URLとなります。指定を行わなかった場合、下書きプレビュー用の共有URLは発行されません。また、下書きではないエントリに対して"yes"を指定しても無効となります。
hatenablog:custom-url要素 ブログエントリのカスタムURLを指定できます。省略した場合カスタムURLの変更は行われません。（省略可）
PUT https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/{entry_id}

<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>新しいタイトル</title>
  <author><name>name</name></author>
  <content type="text/plain">
    ** 新しい本文
  </content>
  <updated>2008-01-01T00:00:00</updated>
  <category term="Scala" />
  <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
  <hatenablog:custom-url xmlns:hatenablog="http://www.hatena.ne.jp/info/xmlns#hatenablog">2009-happy-new-year</hatenablog:custom-url>
</entry>


レスポンス

HTTP/1.1 200 OK
Content-Type: application/atom+xml;type=entry

<?xml version="1.0" encoding="utf-8"?>
<entry>
  <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
  <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/2500000000"/>
  <link rel="alternate" type="text/html" href="http://{ルートURL}/entry/2009-happy-new-year"/>
  <author><name>{はてなID}</name></author>
  <title>新しいタイトル</title>
  <updated>2008-01-01T00:00:00</updated>
  <published>2013-09-02T11:28:23+09:00</published>
  <app:edited>2008-01-01T00:00:00</app:edited>
  <summary type="text"> 新しい本文 </summary>
  <content type="text/x-hatena-syntax">
    ** 新しい本文
  </content>
  <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
    <div class=&quot;section&quot;>
    <h4>新しい本文</h4>
  </hatena:formatted-content>
  <category term="Scala" />
  <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
</entry>

ブログエントリの削除
メンバURIに対してDELETEすることで、ブログエントリを削除できます。

codoc連携記事を削除した際は、記事の有料部分はcodocで下書き（非公開）状態になります。

「寄稿者」権限のブログメンバーは、自身が投稿した下書きエントリのみ削除できます。

リクエスト
DELETE https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry/{entry_id}

レスポンス
HTTP/1.1 200 OK
Content-Type: application/atom+xml;type=entry

固定ページの取得
メンバURIをGETすることで、固定ページを取得できます。

「寄稿者」権限のブログメンバーは自身が投稿した下書きの固定ページのみ取得可能です。

リクエスト
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page/{page_id}

レスポンス
レスポンスは正常時にHTTPステータス200を返します。
レスポンスXML文書はHatena XML名前空間によって拡張されています。
summaryは最大140文字の文書要約が記載されます。
contentにははてなブログに登録されたシンタックスと解釈されたオリジナルな文面が記載されます
type属性には以下の3つの値のいずれかが付与されます。
text/html 見たままモード
text/x-hatena-syntax はてな記法
text/x-markdown マークダウン記法
hatena:formatted-contentには常にエンコードされたhtmlが返却されます。
<?xml version="1.0" encoding="utf-8"?>
<entry>
  <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
  <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/
  ブログID}/atom/page/2500000000"/>
  <link rel="alternate" type="text/html" href="http://{ルートURL}/2013/09/02/112823"/>
  <author><name>{はてなID}</name></author>
  <title>記事タイトル</title>
  <updated>2013-09-02T11:28:23+09:00</updated>
  <published>2013-09-02T11:28:23+09:00</published>
  <app:edited>2013-09-02T11:28:23+09:00</app:edited>
  <summary type="text"> 記事本文 リスト1 リスト2 内容 </summary>
  <content type="text/x-hatena-syntax">
    ** 記事本文
    - リスト1
    - リスト2
    内容
  </content>
  <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
    <div class=&quot;section&quot;>
    <h4>記事本文</h4>

    <ul>
    <li>リスト1</li>
    <li>リスト2</li>
    </ul><p>内容</p>
    </div>
  </hatena:formatted-content>
  <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
</entry>

固定ページの編集
メンバURIに対してXML文書をPUTすることで、固定ページを編集できます。固定ページの記法は編集前に適用されていたものと同じ記法が適用されます。

「寄稿者」権限のブログメンバーは自身が投稿した下書きの固定ページのみ編集可能です。

リクエスト
リクエストXML文書に必要なパラメータは以下です。

title要素 固定ページのタイトル
content要素 記述された固定ページの本文
updated要素 任意項目です。固定ページの投稿日時を指定することができます。
app:control/app:draft要素 固定ページを下書きにするか指定出来ます。"yes"を指定すると下書きになります。指定を行わなかった場合、下書きでないものとみなされます。「寄稿者」権限のブログメンバーは下書きにする必要があります。
app:control/app:preview要素 固定ページが下書きのとき下書きプレビューの共有URLを発行するか指定できます。"yes"を指定すると共有URLが発行され、レスポンスのrel=previewであるatom:link要素のhref属性が共有URLとなります。指定を行わなかった場合、下書きプレビュー用の共有URLは発行されません。また、下書きではない固定ページに対して"yes"を指定しても無効となります。
hatenablog:custom-url要素 固定ページのカスタムURLを指定できます。省略した場合カスタムURLの変更は行われません。（省略可）
PUT https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page/{page_id}

<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>新しいタイトル</title>
  <author><name>name</name></author>
  <content type="text/plain">
    ** 新しい本文
  </content>
  <updated>2008-01-01T00:00:00</updated>
  <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
  <hatenablog:custom-url xmlns:hatenablog="http://www.hatena.ne.jp/info/xmlns#hatenablog">2009-happy-new-year</hatenablog:custom-url>
</entry>


レスポンス

HTTP/1.1 200 OK
Content-Type: application/atom+xml;type=entry

<?xml version="1.0" encoding="utf-8"?>
<entry>
  <id>tag:blog.hatena.ne.jp,2013:blog-{はてなID}-20000000000000-3000000000000000</id>
  <link rel="edit" href="https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page/2500000000"/>
  <link rel="alternate" type="text/html" href="http://{ルートURL}/2009-happy-new-year"/>
  <author><name>{はてなID}</name></author>
  <title>新しいタイトル</title>
  <updated>2008-01-01T00:00:00</updated>
  <published>2013-09-02T11:28:23+09:00</published>
  <app:edited>2008-01-01T00:00:00</app:edited>
  <summary type="text"> 新しい本文 </summary>
  <content type="text/x-hatena-syntax">
    ** 新しい本文
  </content>
  <hatena:formatted-content type="text/html" xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
    <div class=&quot;section&quot;>
    <h4>新しい本文</h4>
  </hatena:formatted-content>
  <app:control>
    <app:draft>no</app:draft>
    <app:preview>no</app:preview>
  </app:control>
</entry>

固定ページの削除
メンバURIに対してDELETEすることで、固定ページを削除できます。

「寄稿者」権限のブログメンバーは、自身が投稿した下書きの固定ページのみ削除できます。

リクエスト
DELETE https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/page/{page_id}

レスポンス
HTTP/1.1 200 OK
Content-Type: application/atom+xml;type=entry

カテゴリ文書
はてなブログAtomPub で利用しているカテゴリ一覧を含むカテゴリ文書を取得できます。

リクエスト
GET https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/category

レスポンス
HTTP/1.1 200 OK
Content-Type: application/atomcat+xml; charset=utf-8

<?xml version="1.0" encoding="utf-8"?>
<app:categories
    xmlns:app="http://www.w3.org/2007/app"
    xmlns:atom="http://www.w3.org/2005/Atom"
    fixed="no">
  <atom:category term="Perl" />
  <atom:category term="Scala" />
  ...
</app:categories>

アクセス可能なユーザ
はてなブログ AtomPub では、ブログのオーナー以外にもブログメンバーがアクセスすることができます。

「管理者」「編集者」権限のブログメンバーはブログオーナーと同じくすべてのAtomPubの操作が可能です。

「寄稿者」権限のブログメンバーは以下の制限があります。

操作	制限
ブログエントリの一覧取得	寄稿者自身が作成した下書きエントリのみ取得可能
ブログエントリの新規投稿	下書きエントリのみ投稿可能
ブログエントリの取得	寄稿者自身が作成した下書きエントリのみ取得可能
ブログエントリの更新	寄稿者自身が作成した下書きエントリのみ編集可能。下書きを公開することはできない
ブログエントリの削除	寄稿者自身が作成した下書きエントリのみ削除可能
固定ページの一覧取得	寄稿者自身が作成した下書き固定ページのみ取得可能
固定ページの新規投稿	下書き固定ページのみ投稿可能
固定ページの取得	寄稿者自身が作成した下書き固定ページのみ取得可能
固定ページの更新	寄稿者自身が作成した下書き固定ページのみ編集可能。下書きを公開することはできない
固定ページの削除	寄稿者自身が作成した下書き固定ページのみ削除可能
カテゴリ文書	取得可能
エラーレスポンス
はてなブログ AtomPub に対して不正な操作を行った場合にエラーレスポンスが返却されます。各エラーレスポンスには次のような意味があります。

400 Bad Request
リクエストが不正な場合に返却されます。リクエストに含まれるXMLの内容等を確認してください。

401 Unauthorized
WSSEによる認証が失敗した際に返却されます。

404 Not Found
存在しないリソースにアクセスした際に返却されます。URLに含まれるはてなID、dateおよびentry_id等を確認してください。

405 Method Not Allowd
リソースに対して許可されていないメソッドによるリクエストを発行した際に返却されます。指定のリソースに対して可能な操作を確認してください。

500 Internal Server Error
はてなブログAtomPub 側でなんらかの問題が発生した際に返却されます。

はてなブログ AtomPub を利用したプログラムの例
Perlを用いた例 (WSSE認証)
CPANモジュールのXML::Atom::ClientはAtomPubクライアントを実装するための、WSSE認証やリクエスト、レスポンスに必要なXML文書の組み立てなどを抽象化したモジュールです。

XML::Atom::Clientを用いて、はてなブログにエントリを投稿するサンプルコードは以下です。

#!/usr/bin/env perl
use strict;
use warnings;
use utf8;

use XML::Atom::Entry;
use XML::Atom::Client;

my $username    = shift or die 'need username';
my $blog_domain = shift or die 'need blog_domain';
my $api_key     = shift;

my $PostURI = "https://blog.hatena.ne.jp/$username/$blog_domain/atom/entry";

my $client = XML::Atom::Client->new;
$client->username($username);
$client->password($api_key);

my $entry = XML::Atom::Entry->new;
$entry->title('テストエントリだよー');
my $content = "
# マークダウンも書けますよ
- こんな
- ふうに
- ね";
$entry->content($content);

my $EditURI = $client->createEntry($PostURI, $entry)
    or die $client->errstr;

print $EditURI;

XML::Atom::Client はWSSE認証を抽象化しているため、username/blog_domain/passwordメソッドでそれぞれをセットするだけで認証を通過できます。また、XML文書の組み立てはXML::Atom::Entryインスタンスを生成して行い、それを最後にXML::Atom::Clientインスタンスに渡せば完了です。

このスクリプトはコマンドラインから、

$ perl atompost.pl はてなID ブログドメイン APIキー

として実行できます。

Perl を用いた例 (OAuth認証)
上記の XML::Atom::Client はOAuth認証には対応していません。ここでは、フレームワークとして Mojolicious::Lite、OAuthライブラリとして OAuth::Lite を利用したサンプルコードを紹介します。

以下のスクリプトを oauth-sample.plとして保存して、以下のように実行します。

$ CONSUMER_KEY='<YOUR CONSUMER KEY>' \\
CONSUMER_SECRET='<YOUR CONSUMER SECRET>' \\
API_URL='<YOUR BLOG API ROOT ENDPOINT>' \\
perl oauth-sample.pl daemon

<YOUR CONSUMER KEY>, <YOUR CONSUMER SECRET> には、自分のOAuthアプリケーションの consumer key, consumer secretを設定してください。<YOUR BLOG API ROOT ENDPOINT> には、サービス文書のURIを設定してください。特に、はてなブログ AtomPub APIは、はてなのOAuth認証における、read_private, write_privateの両方を要求することに注意してください。詳しくは、認証についての章を参照してください。

スクリプトが起動したのち、http://localhost:3000へアクセスしてください。

#!/usr/bin/env perl
use strict;
use warnings;
use utf8;

use Mojolicious::Lite;
use OAuth::Lite::Consumer;
use OAuth::Lite::Token;
use XML::Atom::Feed;
use Encode;

my $consumer_key    = $ENV{CONSUMER_KEY};
my $consumer_secret = $ENV{CONSUMER_SECRET};
my $api_url         = $ENV{BLOG_API_ROOT_ENDPOINT};

if (!($consumer_key && $consumer_secret && $api_url )) {
    print STDERR <<"ENDUSAGE";
Usage:
  CONSUMER_KEY=<YOUR CONSUMER KEY> \\
  CONSUMER_SECRET=<YOUR CONSUMER SECRET> \\
  API_URL=<BLOG API ROOT ENDPOINT> \\
  plackup $0
ENDUSAGE
    exit 1;
}

my $consumer = OAuth::Lite::Consumer->new(
    consumer_key       => $consumer_key,
    consumer_secret    => $consumer_secret,
    site               => q{https://www.hatena.com},
    request_token_path => q{/oauth/initiate},
    access_token_path  => q{/oauth/token},
    authorize_path     => q{https://www.hatena.ne.jp/oauth/authorize},
);

get '/' => sub {
    my $self = shift;
    $self->stash(access_token => $self->session('access_token') || '');
} => 'root';


# リクエストトークン取得から認証用URLにリダイレクトするためのアクション
get '/oauth' => sub {
    my $self = shift;
    $self->stash(consumer => $consumer);

    # リクエストトークンの取得
    my $request_token = $consumer->get_request_token(
        callback_url => q{http://localhost:3000/callback},
        scope        => 'read_private,write_private',
    ) or die $consumer->errstr;
    # セッションへリクエストトークンを保存しておく
    $self->session(request_token => $request_token->as_encoded);

    # 認証用URLにリダイレクトする
    $self->redirect_to( $consumer->url_to_authorize(
        token        => $request_token,
    ) );
};


# 認証からコールバックされ、アクセストークンを取得するためのアクション
get '/callback' => sub {
    my $self = shift;
    $self->stash(consumer => $consumer);
    my $verifier = $self->param('oauth_verifier');
    my $request_token = OAuth::Lite::Token->from_encoded($self->session('request_token'));

    # リクエストトークンとverifierなどを用いてアクセストークンを取得
    my $access_token = $consumer->get_access_token(
        token    => $request_token,
        verifier => $verifier,
    ) or die $consumer->errstr;

    $self->session(request_token => undef);

    # アクセストークンをセッションに記録しておく
    $self->session(access_token  => $access_token->as_encoded);

    $self->redirect_to('/');
} => 'callback';


# アクセストークンを利用して、OAuthに対応したAPIを利用するためのアクション
get '/list' => sub {
    my $self = shift;
    $self->stash(consumer => $consumer);
    my $access_token = OAuth::Lite::Token->from_encoded($self->session('access_token')) or return;

    # access_tokenなどを使ってAPIにアクセスする
    my $res = $consumer->request(
        method => 'GET',
        url    => $api_url . '/entry',
        token  => $access_token,
        params => {},
    ) or die $consumer->errstr;

    my $xml = $res->content;
    my $entries = [
        map {
            my ($link) = map { $_->href } grep { $_->rel eq 'alternate' } $_->link;
            +{ title => ( decode_utf8($_->title) ||'' ), link => ( $link || '' ) }
        } XML::Atom::Feed->new(\$xml)->entries
    ];
    $self->stash(entries => $entries);
} => 'list';

app->start;

__DATA__
@@ root.ep
<a href="/oauth">はてなOAuth認証をする</a>
<br />
<% if ($access_token) { %>
  <a href="/list">エントリ一覧を表示</a>
<% } %>

@@ callback.ep
% my $token = $self->stash('token');
<%= $token->token %></br>
<%= $token->secret %>

@@ list.ep
% my $entries = $self->stash('entries');
<p>エントリ一覧</p>
<ul>
% for my $entry ( @$entries ) {
  <li>
    <a href="<%= $entry->{link} %>"><%= $entry->{title} %></a>
  </li>
% }
</ul>

@@ exception.ep
REQUEST ERROR: <%= $consumer->errstr %> </br>
WWW-Authenticate: <%= $consumer->oauth_res && $consumer->oauth_res->header('www-authenticate') %>

Ruby を用いた例
Ruby gemsで公開されているatomutilというモジュールもXML::Atom::Clientと同様に、AtomPubクライアントを実装するための、WSSE認証やリクエスト、レスポンスに必要なXML文書の組み立てなどを抽象化したモジュールです。

atomutilを用いて、はてなブログにエントリを投稿するサンプルコードは以下です。

#!/usr/bin/env ruby
# -*- encoding: utf-8 -*-

require 'atomutil'

USERNAME    = ARGV[0]
BLOG_DOMAIN = ARGV[1]
API_KEY    = ARGV[2]

POST_URI = "https://blog.hatena.ne.jp/#{USERNAME}/#{BLOG_DOMAIN}/atom/entry"

auth = Atompub::Auth::Wsse.new(
  username: USERNAME,
  password: API_KEY
)
client = Atompub::Client.new(auth: auth)

entry = Atom::Entry.new(
  title: "テストエントリ".encode('BINARY', 'BINARY'),
  content: <<'ENDOFCONENT'.encode('BINARY', 'BINARY'))
*もちろん
- はてな記法も
- 書けます
ENDOFCONENT

p client.create_entry(POST_URI, entry);

このスクリプトはコマンドラインから、

$ ruby atompost.rb はてなID ブログドメイン  APIキー

として実行できます。

Scala を用いた例
ここではJavaのモジュールであるApache Abderaを用いた記事の投稿を、Scalaで実装した例を紹介します。

はてなブログにエントリを投稿するサンプルコードは以下の通りです。

import java.util.Date

import org.apache.abdera.Abdera
import org.apache.abdera.protocol.client.AbderaClient
import org.apache.abdera.ext.wsse.WSSEAuthScheme;

import org.apache.commons.httpclient.UsernamePasswordCredentials;

object AtomPubEntryPost {
  def main(args: Array[String]): Unit = {
    val username = "";
    val blogDomain = "";
    val apiKey = "";

    val abdera = new Abdera
    val abderaClient = new AbderaClient(abdera)
    WSSEAuthScheme.register(abderaClient, true);
    abderaClient.addCredentials("https://blog.hatena.ne.jp", null, "WSSE", new UsernamePasswordCredentials(username, apiKey));

    val factory = abdera.getFactory

    // 記事の記述
    val entry = factory.newEntry
    entry.setTitle("タイトル")
    entry.setUpdated(new Date())
    entry.addAuthor(username)
    entry.setContent("本文")

    // 記事の投稿
    val response = abderaClient.post(s"https://blog.hatena.ne.jp/$username/$blogDomain/atom/entry", entry)
    println("STATUS CODE : " + response.getStatus)
  }
}


依存モジュールは、sbtを用いた場合には、以下のような記述を加えてください。

libraryDependencies ++= Seq (
  "org.apache.abdera" % "abdera-bundle" % "1.1.3",
)

参考
RFC5023 Atom Publishing Protocol
LWP::Authen::Wsse
XML::Atom
XML::Atom::Service
Apache Abdera
Apache Commons Codec
はてなサービスにおけるOAuth
はてなサービスにおけるWSSE認証
はてなXML名前空間
変更履歴
2013年9月4日 リリース
2013年10月03日 OAuth認証に対応
2013年10月15日 OAuth認証を用いたサンプルコードを追加
2013年10月17日 Basic認証に対応/APIのエンドポイントをhttpsに変更(Basic認証が利用できないことを除いて、httpのエンドポイントも引き続き利用できます)
2022年6月16日 ブログメンバーに対応
2023年1月10日 ブログエントリの投稿/編集にcustom-url要素の説明を追加
2023年7月6日 記事の有料販売（codoc連携）の説明を追加
2023年9月14日 固定ページに関連するAPIの説明を追加
2023年10月16日 app:control/app:preview要素についての説明を追加
2023年10月18日 codoc連携記事の編集についての説明を追加
2024年1月11日 updated要素に関する記述を修正