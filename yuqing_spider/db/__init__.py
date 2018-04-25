import datetime


class MysqlDb:
    def __init__(self, cursor):
        self.__cursor = cursor

    def InsertArticle(self, article):
        sql = "INSERT IGNORE INTO `article`(`title`, `thumb_img`, `url`, `description`, `publish_time`, `text`, `create_time`, `source_site`, `body`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        number = self.__cursor.execute(sql, (article['title'],
                                             article['thumb_img'],
                                             article['url'],
                                             article['description'],
                                             article['publish_time'],
                                             article['text'],
                                             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                             article['source_site'],
                                             article['body'],))
        article_id = None
        if number > 0:
            self.__cursor.execute('SELECT last_insert_id()')
            article_id, = self.__cursor.fetchone()

        return number, article_id

    def InsertIndustryArticle(self, industry_id, article_id):
        number = self.__cursor.execute(
            "INSERT INTO `industry_article` (`industry_id`, `article_id`) VALUES (%s,%s)", (industry_id, article_id))
        return number

    def FetchFollowIndustryEmployeeId(self, industry_id):
        """获取关注行业的员工id

        Args:
            industry_id: 行业id
        Returns:
            employee_ids: 员工id列表"""

        number = self.__cursor.execute(
            "SELECT `employee_id` FROM `follow_industry` WHERE `industry_id`=%s AND `is_follow`=1", (industry_id,))
            
        if number:
            row3 = self.__cursor.fetchall()
            return [employee_id for employee_id, in row3]
        else:
            return []

    def InsertEmployeeArticle(self, employee_id, article_id):
        self.__cursor.execute("INSERT INTO `employee_article`(`employee_id`, `article_id`, `is_read`, `is_invalid`) VALUES (%s,%s,%s,%s)", (employee_id, article_id, False, False))

    def FetchCompanyIdByStockId(self, stock_id):
        company_id = None
        number = self.__cursor.execute("SELECT `id`FROM `company` WHERE `stock_id`=%s", (stock_id, ))
        if number:
            company_id, = self.__cursor.fetchone()
        
        return number, company_id
    
    def FetchCompanyIdByShortName(self, short_name):
        company_id = None
        number = self.__cursor.execute("SELECT `id`FROM `company` WHERE `short_name`=%s", (short_name, ))
        if number:
            company_id, = self.__cursor.fetchone()
        
        return number, company_id

    def InsertCompanyArticle(self, company_id, article_id):
        number = self.__cursor.execute("INSERT INTO `company_article`(`company_id`, `article_id`) VALUES (%s,%s)", (company_id, article_id))

        return number

    def FetchFollowCompanyEmployeeId(self, company_id):
        number = self.__cursor.execute(
            "SELECT `employee_id` FROM `follow_company` WHERE `company_id`=%s AND `is_follow`=1", (company_id,))

        if number:
            row3 = self.__cursor.fetchall()
            return [employee_id for employee_id, in row3]
        else:
            return []