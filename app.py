from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# 优先用环境变量DATABASE_URL（如线上Postgres），否则用本地sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///customers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

cloudinary.config(
    cloud_name = 'dhjim7xbr',
    api_key = '149872547298524',
    api_secret = 'QItNLkUdG54eFYrFXfVPfCo74eM',
    secure = True
)

# 客户信息模型
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_name = db.Column(db.String(100), nullable=False)
    wechat_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    preferred_time = db.Column(db.String(200))
    competition_experience = db.Column(db.Text)
    needs = db.Column(db.Text)
    recommended_class = db.Column(db.String(100))
    trial_class_time = db.Column(db.Date)  # 只存日期
    future_trial_time = db.Column(db.Date)  # 未来预定字符串
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 试课记录模型
class TrialRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    child_name = db.Column(db.String(100), nullable=False)
    wechat_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    trial_time = db.Column(db.Date)
    trial_time_slot = db.Column(db.String(50))
    future_trial_time = db.Column(db.String(100))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 班级信息模型
class ClassInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    grade_level = db.Column(db.String(50))
    time_slots = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hero-medals.jpg')
def hero_medals():
    """Serve hero background image from project root for consultation page."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hero-medals.jpg')
    if not os.path.isfile(path):
        return '', 404
    return send_file(path, mimetype='image/jpeg')

@app.route('/submit', methods=['POST'])
def submit():
    print("submit被调用")
    try:
        data = request.form
        print("收到表单数据:", data)
        # 推荐所有适用年级包含该年级的班级
        recommended_classes = recommend_classes(data['grade'])
        # 只取第一个推荐班型的名字（如有）
        recommended_class_name = recommended_classes[0]['name'] if recommended_classes else None

        from datetime import datetime
        trial_class_time_str = data.get('trial_class_time')
        trial_class_time = None
        if trial_class_time_str:
            try:
                trial_class_time = datetime.strptime(trial_class_time_str, '%Y-%m-%d').date()
            except Exception:
                trial_class_time = None

        # competition_experience: DB column unchanged; UI now collects 孩子学校 (school) to avoid schema migration
        customer = Customer(
            child_name=data['child_name'],
            wechat_name=data['wechat_name'],
            grade=data['grade'],
            preferred_time=data['preferred_time'],
            competition_experience=data.get('competition_experience', ''),  # now used for school name
            needs=data['needs'],
            recommended_class=recommended_class_name,  # 写入推荐班型
            trial_class_time=trial_class_time
        )
        db.session.add(customer)
        db.session.commit()

        # 返回新客户ID，便于后续试课安排
        return jsonify({
            'success': True,
            'recommended_classes': recommended_classes,
            'customer_id': customer.id
        })
    except Exception as e:
        import sys
        print("/submit异常：", e, file=sys.stderr)
        raise

@app.route('/admin')
def admin():
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('admin.html', customers=customers)

@app.route('/admin/classes')
def admin_classes():
    classes = ClassInfo.query.all()
    return render_template('admin_classes.html', classes=classes)

@app.route('/admin/classes/save', methods=['POST'])
def admin_classes_save():
    try:
        print("🔍 收到表单内容:", dict(request.form))
        print("🔍 收到文件内容:", request.files)
        name = request.form.get('name')
        grade_level = request.form.get('grade_level')  # 逗号分隔字符串
        description = request.form.get('description')
        image = request.files.get('image')
        time_slots = request.form.get('time_slots')

        # 检查必填项
        if not name:
            return jsonify(success=False, message='班级名称不能为空')
        if not grade_level:
            return jsonify(success=False, message='请至少选择一个年级')
        if not description:
            return jsonify(success=False, message='班级描述不能为空')

        # 处理图片保存
        image_url = None
        if image and image.filename:
            try:
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result['secure_url']
                print("✅ Cloudinary上传结果:", upload_result)
            except Exception as e:
                print(f"Error uploading image to Cloudinary: {str(e)}")
                return jsonify(success=False, message='图片上传失败')

        # 保存到数据库
        try:
            print("📝 即将保存到数据库:", name, grade_level, description, image_url, time_slots)
            new_class = ClassInfo(
                name=name,
                grade_level=grade_level,
                description=description,
                image_url=image_url,
                time_slots=time_slots
            )
            db.session.add(new_class)
            db.session.commit()
            return jsonify(success=True)
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify(success=False, message='数据库保存失败')
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify(success=False, message='系统错误，请稍后重试')

@app.route('/admin/dashboard')
def admin_dashboard():
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    classes = ClassInfo.query.all()
    return render_template('admin_dashboard.html', customers=customers, classes=classes)

@app.route('/api/edit_customer', methods=['POST'])
def edit_customer():
    customer_id = request.form.get('id')
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify(success=False, message='客户不存在')

    customer.child_name = request.form.get('child_name')
    customer.wechat_name = request.form.get('wechat_name')
    customer.grade = request.form.get('grade')
    customer.preferred_time = request.form.get('preferred_time')
    customer.competition_experience = request.form.get('competition_experience')
    customer.needs = request.form.get('needs')
    customer.recommended_class = request.form.get('recommended_class')
    customer.future_trial_time = request.form.get('trial_time')

    db.session.commit()
    return jsonify(success=True)

@app.route('/api/delete_customer', methods=['POST'])
def delete_customer():
    customer_id = request.form.get('id')
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify(success=False, message='客户不存在')
    db.session.delete(customer)
    db.session.commit()
    return jsonify(success=True)

@app.route('/admin/classes/delete/<int:id>', methods=['POST'])
def delete_class(id):
    class_obj = ClassInfo.query.get(id)
    if not class_obj:
        return jsonify(success=False, message='班级不存在')
    db.session.delete(class_obj)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/delete_customers', methods=['POST'])
def delete_customers():
    ids = request.get_json().get('ids', [])
    if not ids:
        return jsonify(success=False, message='未提供ID')
    try:
        Customer.query.filter(Customer.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e))

def recommend_classes(grade):
    # 查询所有包含该年级的班级，使用更精确的匹配
    classes = ClassInfo.query.filter(
        (ClassInfo.grade_level == grade) |  # 完全匹配
        (ClassInfo.grade_level.like(f"{grade},%")) |  # 开头匹配
        (ClassInfo.grade_level.like(f"%,{grade},%")) |  # 中间匹配
        (ClassInfo.grade_level.like(f"%,{grade}"))  # 结尾匹配
    ).all()
    result = []
    for c in classes:
        result.append({
            'name': c.name,
            'description': c.description,
            'image_url': c.image_url,
            'time_slots': c.time_slots
        })
    return result

# 保证无论本地还是线上都能自动建表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 