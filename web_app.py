from flask import Flask, request, session, redirect, url_for, render_template_string
import enhanced_library as lib

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-secret'

REGISTER_FORM = '''
<h2>读者注册</h2>
<form method="post">
  借书证号: <input type="text" name="library_card_no" required><br>
  姓名: <input type="text" name="name" required><br>
  密码: <input type="password" name="password" required><br>
  <input type="submit" value="注册">
</form>
<p style="color:red;">{{ message }}</p>
<a href="{{ url_for('login') }}">已有账号？登录</a>
'''

LOGIN_FORM = '''
<h2>登录</h2>
<form method="post">
  账号/借书证号: <input type="text" name="username" required><br>
  密码: <input type="password" name="password" required><br>
  <input type="submit" value="登录">
</form>
<p style="color:red;">{{ message }}</p>
<a href="{{ url_for('register') }}">注册新账号</a>
'''

DASHBOARD_PAGE = '''
<h2>欢迎, {{ user.get('name', user.get('username')) }}!</h2>
<p>角色: {{ user['role'] }}</p>
<ul>
  <li><a href="{{ url_for('books') }}">查看图书</a></li>
  <li><a href="{{ url_for('logout') }}">退出登录</a></li>
</ul>
'''

BOOK_LIST_PAGE = '''
<h2>图书列表</h2>
<ul>
{% for b in books %}
  <li>{{ b['title'] }} - {{ b['author'] }} (ISBN: {{ b['isbn'] }})</li>
{% endfor %}
</ul>
<a href="{{ url_for('dashboard') }}">返回</a>
'''

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        card_no = request.form.get('library_card_no', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        if card_no and name and password:
            success, msg = lib.register_reader(card_no, name, password)
            if success:
                return redirect(url_for('login'))
            message = msg
        else:
            message = '请完整填写所有字段'
    return render_template_string(REGISTER_FORM, message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = lib.authenticate_user(username, password)
        if user:
            session['user'] = user
            return redirect(url_for('dashboard'))
        message = '用户名或密码错误'
    return render_template_string(LOGIN_FORM, message=message)

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_PAGE, user=user)

@app.route('/books')
def books():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    book_list = lib.search_books()
    return render_template_string(BOOK_LIST_PAGE, books=book_list)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
