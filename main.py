from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import users
from time import time
from google.appengine.ext.webapp import template

class DiversityRecord(db.Model):
    """
    Record of a single diversity measurement
    """
    impact_rating = db.IntegerProperty()
    species_count = db.IntegerProperty()
    sampled_area = db.FloatProperty()
    month = db.StringProperty()
    year = db.IntegerProperty()
    description = db.TextProperty()
    teacher = db.StringProperty()
    school = db.StringProperty()

class Teacher(db.Model):
    """
    Record of valid teacher names
    """
    name = db.TextProperty()

class School(db.Model):
    """
    Record of valid school names
    """
    name = db.TextProperty()

class MainPageHandler(webapp.RequestHandler):
    """
    Main page with form to view or filter data
    """
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            error_message = self.request.get('error_message')
            teachers = db.GqlQuery('SELECT * FROM Teacher')
            schools = db.GqlQuery('SELECT * FROM School')
            template_values = {'error_message': error_message,
                               'teachers': teachers,
                               'schools': schools}
            self.response.out.write(template.render('mainpage.html', template_values))

    def post(self):
        self.get()

class DataEntryPageHandler(webapp.RequestHandler):
    """
    Data entry page with form to enter new data points and buttons to
    add new teachers or schools.
    """
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            error_message = self.request.get('error_message')
            teachers = db.GqlQuery('SELECT * FROM Teacher')
            schools = db.GqlQuery('SELECT * FROM School')
            template_values = {'error_message': error_message,
                               'teachers': teachers,
                               'schools': schools}
        self.response.out.write(template.render('dataentrypage.html', template_values))

    def post(self):
        self.get()

class NewRecordHandler(webapp.RequestHandler):
    """
    Validates and stores a new diversity record
    """
    def is_numeric(self, numeric_text):
        """
        Verify that a string can be converted to an integer or float
        """
        try:
            float(numeric_text) if '.' in numeric_text else int(numeric_text)
            return True
        except:
            return False

    def post(self):
        error_message = ''
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            sampled_area = self.request.get('sampled_area')
            species_count = self.request.get('species_count')
            teacher = self.request.get('teacher')
            school = self.request.get('school')
            month = self.request.get('month')
            year = self.request.get('year')
            if teacher == "None":
                error_message = 'Invalid teacher name'
            elif school == "None":
                error_message = 'Invalid school name'
            elif month == "0":
                error_message = 'Invalid month'
            elif year == "0":
                error_message = 'Invalid year'
            elif not self.is_numeric(sampled_area):
                error_message = 'Invalid sampled area'
            elif not self.is_numeric(species_count):
                error_message = 'Invalid species count'
            else:
                diversity_record = DiversityRecord()
                diversity_record.sampled_area = float(sampled_area)
                diversity_record.species_count = int(species_count)
                diversity_record.impact_rating = int(self.request.get('impact_rating'))
                diversity_record.month = month
                diversity_record.year = int(year)
                diversity_record.description = self.request.get('description')
                diversity_record.teacher = teacher
                diversity_record.school = school
                diversity_record.put()
                error_message = 'Success - record added'
            redirect_string = '/?error_message=' + error_message
            self.redirect(redirect_string)

class ViewRecordsHandler(webapp.RequestHandler):
    """
    Displays a subset of the records
    """
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            teacher = self.request.get('teacher')
            school = self.request.get('school')
            month = self.request.get('month')
            year = self.request.get('year')
            query_string = "SELECT * FROM DiversityRecord"
            where_clause = False
            if month != "0":
                query_string = query_string + " WHERE month = '" + month + "'"
                where_clause = True
            if year != "0":
                if where_clause:
                    query_string = query_string + " AND year = " + year
                else:
                    query_string = query_string + " WHERE year = " + year
                    where_clause = True
            if teacher != "0":
                if where_clause:
                    query_string = query_string + " AND teacher = '" + teacher + "'"
                else:
                    query_string = query_string + " WHERE teacher = '" + teacher + "'"
                    where_clause = True
            if school != "0":
                if where_clause:
                    query_string = query_string + " AND school = '" + school + "'"
                else:
                    query_string = query_string + " WHERE school = '" + school + "'"
                    where_clause = True
            records = db.GqlQuery(query_string)
            records_by_impact = [0,0,0,0,0,0,0,0,0,0,0]
            species_by_impact = [0,0,0,0,0,0,0,0,0,0,0]
            averages_by_impact = [0,0,0,0,0,0,0,0,0,0,0]
            for record in records:
                impact_rating = record.impact_rating
                species_count = record.species_count
                records_by_impact[impact_rating] += 1
                species_by_impact[impact_rating] += species_count
            max_yaxis = 0
            chart_values = ''
            for i in range(11):
                if records_by_impact[i] > 0:
                    averages_by_impact[i] = species_by_impact[i] / float(records_by_impact[i])
                else:
                    averages_by_impact[i] = 0
                chart_values += ',' + str(averages_by_impact[i])
                if averages_by_impact[i] > max_yaxis:
                    max_yaxis = averages_by_impact[i]
            chart_values = chart_values[1:]
            chart_url_string = '<img src="http://chart.apis.google.com/chart?chxr=0,0,%s&chxs=0,676767,10.833,0,t,676767&chxt=y,x&chbh=a,6&chs=500x300&cht=bvg&chco=A2C180,3D7930&chds=0,%s,-3.333,100&chd=t1:%s|-1&chma=|0,2&chtt=Average+species+diversity+by+human+impact rating&chts=676767,20" width="500" height="300" alt="Species Diversity" />' % (max_yaxis, max_yaxis, chart_values)
            template_values = {'records': records,
                               'chart_url_string': chart_url_string}
            self.response.out.write(template.render('recordspage.html', template_values))

class NewTeacherSchoolHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            teacher = self.request.get('teacher')
            school = self.request.get('school')
            message = ''
            if teacher:
                teachers = db.GqlQuery('SELECT * FROM Teacher')
                is_in_list = False
                for each_teacher in teachers:
                    if each_teacher.name == teacher:
                        is_in_list = True
                if not is_in_list:
                    new_teacher = Teacher()
                    new_teacher.name = teacher
                    new_teacher.put()
                    message = 'Added %s to the list of teachers' % teacher
                else:
                    message = '%s was already in the list of teachers' % teacher
            if school:
                schools = db.GqlQuery('Select * FROM School')
                is_in_list = False
                for each_school in schools:
                    if each_school.name == school:
                        is_in_list = True
                if not is_in_list:
                    new_school = School()
                    new_school.name = school
                    new_school.put()
                    message = 'Added %s to the list of schools' % school
                else:
                    message = '%s was already in the list of schools' % school
            template_values = {'message': message}
            self.response.out.write(template.render('newteacherschoolpage.html', template_values))

    def get(self):
        self.post()


def main():
    application = webapp.WSGIApplication([('/', MainPageHandler),
                                          ('/addrecord', NewRecordHandler),
                                          ('/viewrecords', ViewRecordsHandler),
                                          ('/new', NewTeacherSchoolHandler),
                                          ('/data', DataEntryPageHandler)],
                                         debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
