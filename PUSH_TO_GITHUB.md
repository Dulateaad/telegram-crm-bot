# Инструкция по загрузке в GitHub

## Вариант 1: Использование Personal Access Token (рекомендуется)

### Шаг 1: Создайте Personal Access Token

1. Откройте https://github.com/settings/tokens
2. Нажмите **"Generate new token"** → **"Generate new token (classic)"**
3. Название: `telegram-crm-bot`
4. Выберите срок действия (например, 90 дней или No expiration)
5. Отметьте права доступа:
   - ✅ `repo` (полный доступ к репозиториям)
6. Нажмите **"Generate token"**
7. **Скопируйте токен** (он показывается только один раз!)

### Шаг 2: Создайте репозиторий на GitHub

1. Откройте https://github.com/new
2. Repository name: `telegram-crm-bot`
3. Description: `Telegram CRM Bot for order management with Firebase integration`
4. Выберите Public или Private
5. **НЕ** добавляйте README, .gitignore или лицензию
6. Нажмите **"Create repository"**

### Шаг 3: Загрузите файлы

Выполните команды (замените `YOUR_TOKEN` на ваш токен):

```bash
cd /Users/dulat/telegram-bot-crm

# Убедитесь, что remote настроен на HTTPS
git remote set-url origin https://github.com/Dulateaad/telegram-crm-bot.git

# При push введите:
# Username: Dulateaad
# Password: ВСТАВЬТЕ_ВАШ_ТОКЕН_СЮДА
git push -u origin main
```

**Или используйте токен напрямую в URL:**

```bash
git remote set-url origin https://YOUR_TOKEN@github.com/Dulateaad/telegram-crm-bot.git
git push -u origin main
```

---

## Вариант 2: Настройка SSH ключа

### Шаг 1: Проверьте наличие SSH ключа

```bash
ls -la ~/.ssh/id_ed25519.pub
# или
ls -la ~/.ssh/id_rsa.pub
```

### Шаг 2: Если ключа нет - создайте его

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Нажмите Enter для всех вопросов
```

### Шаг 3: Добавьте ключ в GitHub

```bash
# Скопируйте публичный ключ
cat ~/.ssh/id_ed25519.pub
# или
cat ~/.ssh/id_rsa.pub
```

1. Откройте https://github.com/settings/keys
2. Нажмите **"New SSH key"**
3. Title: `MacBook Air`
4. Вставьте скопированный ключ
5. Нажмите **"Add SSH key"**

### Шаг 4: Подтвердите подключение

```bash
ssh -T git@github.com
# Введите "yes" когда спросит
```

### Шаг 5: Загрузите файлы

```bash
cd /Users/dulat/telegram-bot-crm
git remote set-url origin git@github.com:Dulateaad/telegram-crm-bot.git
git push -u origin main
```

---

## Быстрый способ (если репозиторий уже создан)

Если репозиторий уже создан на GitHub, просто выполните:

```bash
cd /Users/dulat/telegram-bot-crm
git remote set-url origin https://github.com/Dulateaad/telegram-crm-bot.git
git push -u origin main
```

Когда попросит пароль - вставьте ваш Personal Access Token.

---

## Проверка

После успешной загрузки откройте:
https://github.com/Dulateaad/telegram-crm-bot

Вы должны увидеть все файлы проекта!

