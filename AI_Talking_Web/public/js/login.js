// 登录功能的简单实现
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const usernameInput = document.getElementById('loginUsername');
        const passwordInput = document.getElementById('loginPassword');
        
        const username = usernameInput.value;
        const password = passwordInput.value;
        
        if (!username || !password) {
            loginError.textContent = '请输入用户名和密码';
            return;
        }
        
        try {
            // 调用登录API
            const response = await fetch('http://localhost:8000/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    password: password
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                // 保存token到localStorage
                localStorage.setItem('token', data.access_token);
                // 隐藏登录模态框
                const loginModal = document.getElementById('loginModal');
                if (loginModal) {
                    loginModal.style.display = 'none';
                }
            } else {
                const errorData = await response.json();
                loginError.textContent = errorData.detail || '登录失败，请检查用户名和密码';
            }
        } catch (error) {
            console.error('登录失败:', error);
            loginError.textContent = '登录失败，服务器连接错误';
        }
    });
}

// 注册按钮点击事件
const registerBtn = document.getElementById('registerBtn');
if (registerBtn) {
    registerBtn.addEventListener('click', () => {
        alert('注册功能正在开发中');
    });
}

// 检查是否已登录
const token = localStorage.getItem('token');
if (token) {
    const loginModal = document.getElementById('loginModal');
    if (loginModal) {
        loginModal.style.display = 'none';
    }
}