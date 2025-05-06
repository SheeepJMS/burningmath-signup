from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 客户信息模型
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_name = db.Column(db.String(100), nullable=False)
    wechat_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    preferred_time = db.Column(db.String(200))
    competition_experience = db.Column(db.Text)
    needs = db.Column(db.Text)
    recommended_class = db.Column(db.String(100))  # 初步推荐班级
    trial_class_time = db.Column(db.DateTime)
    future_trial_time = db.Column(db.String(100))
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

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form
    # 推荐所有适用年级包含该年级的班级
    recommended_classes = recommend_classes(data['grade'])
    # 只取第一个推荐班型的名字（如有）
    recommended_class_name = recommended_classes[0]['name'] if recommended_classes else None

    customer = Customer(
        child_name=data['child_name'],
        wechat_name=data['wechat_name'],
        grade=data['grade'],
        preferred_time=data['preferred_time'],
        competition_experience=data['competition_experience'],
        needs=data['needs'],
        recommended_class=recommended_class_name  # 写入推荐班型
    )
    db.session.add(customer)
    db.session.commit()

    # 返回新客户ID，便于后续试课安排
    return jsonify({
        'success': True,
        'recommended_classes': recommended_classes,
        'customer_id': customer.id
    })

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
                image_folder = os.path.join('static', 'class_images')
                os.makedirs(image_folder, exist_ok=True)
                image_path = os.path.join(image_folder, image.filename)
                image.save(image_path)
                image_url = f'/static/class_images/{image.filename}'
            except Exception as e:
                print(f"Error saving image: {str(e)}")
                return jsonify(success=False, message='图片保存失败')

        # 保存到数据库
        try:
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

@app.route('/api/set_trial_time', methods=['POST'])
def set_trial_time():
    customer_id = request.form.get('customer_id')
    trial_time = request.form.get('trial_time')  # 字符串，如"2024-05-10 10-12"或"2024年5月上旬"

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify(success=False, message='客户不存在')

    customer.future_trial_time = trial_time
    db.session.commit()
    return jsonify(success=True)

def recommend_classes(grade):
    # 查询所有包含该年级的班级
    classes = ClassInfo.query.filter(ClassInfo.grade_level.like(f"%{grade}%")).all()
    result = []
    for c in classes:
        result.append({
            'name': c.name,
            'description': c.description,
            'image_url': c.image_url,
            'time_slots': c.time_slots
        })
    return result

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 