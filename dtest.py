#!/usr/bin/evn python
# -*- coding:utf-8 -*-

# test

import datetime, time
import mysql.connector
import xlwt
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')

# 默认样式
default_style = xlwt.easyxf('''
  pattern: pattern solid;
  borders: left 1, right 1, top 1, bottom 1;
  align: horiz center''',
  num_format_str='0,000.00')

# 标题栏样式
title_style = xlwt.easyxf('''
  pattern: pattern solid, fore_colour yellow;
  font: name Times New Roman, color-index black, bold on;
  borders: left 1, right 1, top 1, bottom 1;
  align: horiz center''',
  num_format_str='0,000.00')

# 时间格式样式
time_style = xlwt.easyxf(num_format_str='YYYY-MM-DD h:mm:ss')

def get_sql():
  '''
  创建需要的sql语句
  '''
  sql = '''
SELECT 
  loan.repay_date '到期日期',
  loan.loan_order_no '借款编号',
  auth.real_name  '姓名',
  u.mobile '手机号',
  auth.id_card  '身份证',
  TO_BASE64 (risk.risk_content) '身份证地址',
  auth.age '年龄',
  (SELECT d.value FROM dictionary d WHERE d.code=auth.sex AND TYPE ='sex') '性别',
  loan.loan_amount '借款金额',
  loan.each_term '借款期限',
  loan.apply_time '申请时间',
  loan.loan_time '放款时间',
  repay.overdue_days '逾期天数',
  repay.overdue_amount '累计罚息',
  detail.qq 'QQ',
  detail.residential_area '居住地区',
  detail.residential_address '居住详细地址',
  detail.company_name '公司名称',
  detail.work_area '工作地区',
  detail.work_address '工作详细地址',
  detail.company_phone '单位电话',
  detail.relatives_name '亲属联系人姓名',
  (SELECT d.value FROM dictionary d WHERE d.code=detail.relatives_type AND TYPE ='re_contact_type') '亲属联系人关系',
  detail.relatives_mobile '亲属联系人电话',
  detail.social_name '社会联系人姓名',
  (SELECT d.value FROM dictionary d WHERE d.code=detail.social_type AND TYPE ='so_contact_type') '社会联系人关系',
  detail.social_phone '社会联系人电话' ,
  detail.contact_list '通讯录'  
FROM
  loan_order loan
  LEFT JOIN user_auth_info auth ON loan.user_id = auth.user_id
  LEFT JOIN USER u ON loan.user_id = u.id
  LEFT JOIN risk_credit_info risk ON loan.user_id = risk.user_id AND risk.risk_channel IN('faceid','junyufr')AND risk.risk_channel_interface IN('ocridcard','ocr')
  LEFT JOIN repay_plan repay ON loan.id=repay.loan_order_id 
  LEFT JOIN loan_detail_info detail ON loan.id=detail.loan_order_id
WHERE  loan.status ='7'
and    repay.overdue_days<16
AND    loan.repay_date BETWEEN  DATE_SUB(CURDATE(),INTERVAL 90 DAY) AND DATE_SUB(CURDATE(),INTERVAL 1 DAY)
ORDER BY loan.repay_date DESC
'''

  return sql

def get_title(cursor):
  '''
  通过游标获得excel文件title
  '''
  return cursor.column_names

def get_select_data(cursor):
  '''
  通过游标获得数据列表(list)
  '''
  return [row for row in cursor]

def create_excel_title(work_sheet, title, title_style=None):
  '''
  生产exceltitle
  '''
  if not title_style:
    title_style = default_style
  for col_index, col_name in enumerate(title):
    work_sheet.write(0, col_index, col_name, title_style)
  return work_sheet

def create_excel_body(work_sheet, body, body_style=None):
  '''
  生成excel body信息
  '''
  if not title_style:
    body_style = default_style
  for row_num, row_data in enumerate(data, 1):
    for col_index, col_value in enumerate(row_data):
      work_sheet.write(row_num, col_index, col_value)
  return work_sheet

def get_col_max_length(data, title):
  '''
  获得数据每列最大值长度
  '''
  col_len = map(len, map(str, title))
  func = lambda x, y: y if y>x else x
  for row in data:
    row_len = map(len, map(str, row))
    col_len = map(func, col_len, row_len)
  return col_len

def set_work_sheet_col_len(work_sheet, max_len):
  '''
  设置列长度
  '''
  for col, len in enumerate(max_len):
    work_sheet.col(col).width = 256 * (len + 1)
  return work_sheet
      

if __name__ == '__main__':
  info = {
    'host'    :'*******',
    'user'    :'baobiao',
    'password':'********',
    'database':'*******'
  }
  conn = mysql.connector.connect(**info)
  cursor = conn.cursor()
  sql = get_sql()
  cursor.execute(sql)
  # 获得excel的title
  title = get_title(cursor)
  # 获得需要的数据
  data = get_select_data(cursor)
  # 获得每一列的最大长度
  max_len = get_col_max_length(data, title)
  work_book = xlwt.Workbook(encoding='utf-8')
  # 创建一个excel模板
  work_sheet = work_book.add_sheet('查询数据')
  # 生成excel title
  work_sheet = create_excel_title(work_sheet, title, title_style)
  # 生成 excel 数据
  work_sheet = create_excel_body(work_sheet, data)
  # 设置每一列适当的长度
  work_sheet = set_work_sheet_col_len(work_sheet, max_len)
  # 保存 excel
  work_book.save('data_{time}_运营数据统计报表.xls'.format(time=time.strftime('%Y-%m-%d', time.localtime(time.time()))))

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr

import smtplib

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr(( \
        Header(name, 'utf-8').encode(), \
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))
from_addr = '*******'
password = '******'
to_addr = ['daicl@gszygroup.com']
smtp_server = 'smtp.exmail.qq.com'

msg = MIMEMultipart()
msg['From'] = _format_addr(u'运维自动报表 <%s>' % from_addr)
msg['To'] = _format_addr(u'运营 <%s>' % to_addr)
msg['Subject'] = Header(u'日数据报表-运营数据统计报表', 'utf-8').encode()

# add MIMEText:
msg.attach(MIMEText('HI，all：相关报表见邮件附件，请查收！', 'plain', 'utf-8'))

# add file:
with open(('data_%s_运营数据统计报表.xls' % time.strftime('%Y-%m-%d', time.localtime(time.time()))), 'rb') as f:
    mime = MIMEBase('image', 'xls', filename=('data_%s_运营数据统计报表.xls' % time.strftime('%Y-%m-%d', time.localtime(time.time()))))
    mime.add_header('Content-Disposition', 'attachment', filename=('data_%s_运营数据统计报表.xls' % time.strftime('%Y-%m-%d', time.localtime(time.time()))))
    mime.add_header('Content-ID', '<0>')
    mime.add_header('X-Attachment-Id', '0')
    mime.set_payload(f.read())
    encoders.encode_base64(mime)
    msg.attach(mime)

server = smtplib.SMTP_SSL(smtp_server, 465)
server.set_debuglevel(1)
server.login(from_addr, password)
server.sendmail(from_addr, to_addr, msg.as_string())
server.quit()
