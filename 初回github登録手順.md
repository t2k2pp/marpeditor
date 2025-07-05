# 初回GitHub登録手順

このドキュメントでは、ローカルのプロジェクトを初めてGitHubリポジトリに登録する際の手順を説明します。

## 1. Gitリポジトリの初期化

プロジェクトのルートディレクトリで、以下のコマンドを実行し、Gitリポジトリを初期化します。

```bash
git init
```

## 2. リモートリポジトリの追加

GitHub上に作成したリポジトリのURLをリモートとして追加します。`<YOUR_REPOSITORY_URL>` の部分を実際のGitHubリポジトリのURLに置き換えてください。

```bash
git remote add origin <YOUR_REPOSITORY_URL>
```

例:
```bash
git remote add origin https://github.com/t2k2pp/marpeditor.git
```

## 3. ファイルのステージング

現在のディレクトリにあるすべてのファイルをステージングエリアに追加します。

```bash
git add .
```

## 4. コミット

ステージングした変更をローカルリポジトリにコミットします。コミットメッセージは、変更内容がわかるように記述します。

```bash
git commit -m "Initial commit"
```

もし、上記コマンドでエラーが発生する場合は、コミットメッセージをファイルから読み込む方法を試してください。

1.  `commit_message.txt` というファイルを作成し、コミットメッセージを記述します（例: `Initial commit`）。
2.  以下のコマンドでコミットします。

    ```bash
    git commit -F commit_message.txt
    ```

## 5. リモートリポジトリへのプッシュ

ローカルリポジトリのコミットをリモートリポジトリ（GitHub）にプッシュします。初回プッシュ時は `-u` オプションを付けて、ローカルのブランチとリモートのブランチを関連付けます。

```bash
git push -u origin master
```

### 認証について

`git push` の際に認証が求められる場合があります。通常、Windows環境ではGit Credential Managerが自動的に認証情報を管理してくれるため、明示的な入力なしにプッシュが成功することがあります。もし認証が求められた場合は、GitHubのユーザー名とパスワード、またはパーソナルアクセストークンを入力してください。
