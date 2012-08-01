from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models

class Profiles(models.Model):
	Username = models.CharField(max_length=30,unique=True)
	Email = models.CharField(max_length=254)
	Password = models.CharField(max_length=81)
	FailedLoginAttempts = models.PositiveSmallIntegerField()
	IsAdmin = models.BooleanField()
	NumberOfStars = models.PositiveSmallIntegerField()
	SubStars = models.PositiveSmallIntegerField()
	StarImage = models.PositiveSmallIntegerField()
	StarIndicators = models.CharField(max_length=1000)
	CreatedAt= models.DateTimeField(auto_now_add=True)
	UpdatedAt = models.DateTimeField(auto_now=True)
	
	def clean(self):
		data = self.Username
		# No unicode characters
		if data and len(data) > 0 and not data.encode('ascii', 'replace').isalnum():
			raise ValidationError("Username can only contain alphanumeric characters.")
		email = self.Email
		validate_email(email)
		data = self.NumberOfStars
		if not (data >= 1 and data <= 10):
			raise ValidationError("Number of stars can only be between 1 and 10 (inclusive).")
		data = self.SubStars
		if not (data == 1 or data == 2 or data == 4):
			raise ValidationError("Sub stars can only be 1, 2, or 4.")
		# Change indicators to decimals if not properly defined (i.e. 0.5, 1.0, 1.5, ...)
		data = self.StarIndicators
		list = data.split(',')
		if len(list) != self.NumberOfStars * self.SubStars:
			indicators = ''
			for i in range(self.NumberOfStars):
				for j in range(self.SubStars):
					indicators += str(i + (float(j + 1) / self.SubStars))
					indicators += ','
			self.StarIndicators = indicators[0:-1]

class PropertyTypes(models.Model):
	Description = models.CharField(max_length=50,unique=True)
	TableName = models.CharField(max_length=50)

	class Meta:
		unique_together = ('Description', 'TableName')

class People(models.Model):
	Name = models.CharField(max_length=100,unique=True)
	UrlName = models.CharField(max_length=100,null=True,blank=True,unique=True)
	CreatedAt= models.DateTimeField(auto_now_add=True)
	UpdatedAt = models.DateTimeField(auto_now=True)
	
	def clean(self):
		urlname = ''
		hasAlNum = False
		# Form UrlName and check basic requirements
		name = self.Name.encode('ascii', 'replace')
		if name and len(name) > 0:
			for char in name:
				if not hasAlNum and char.isalnum():
					hasAlNum = True
				if char.isalnum():
					urlname += char.lower()
				# Replace unicode characters with ~
				elif char == '?':
					urlname += '~'
				elif char.isspace():
					urlname += '_'
		if hasAlNum and len(urlname) > 0:
			self.UrlName = urlname
		else:
			raise ValidationError("Name must contain at least one alphanumeric character.")
	
class Genres(models.Model):
	Description = models.CharField(max_length=50,unique=True)
	CreatedAt= models.DateTimeField(auto_now_add=True)
	UpdatedAt = models.DateTimeField(auto_now=True)
	
	def clean(self):
		data = self.Description
		if data and len(data) > 0 and not data.encode('ascii', 'replace').isalnum():
			raise ValidationError("Description can only contain alphanumeric characters.")

class ConsumeableTypes(models.Model):
	Description = models.CharField(max_length=50,unique=True)

class Sources(models.Model):
	ProfileId = models.ForeignKey(Profiles,related_name='+')
	ConsumeableTypeId = models.ForeignKey(ConsumeableTypes,related_name='+')
	Description = models.CharField(max_length=50)

	class Meta:
		unique_together = ('ProfileId', 'ConsumeableTypeId', 'Description')
	
class Movies(models.Model):
	Title = models.CharField(max_length=100)
	UrlTitle = models.CharField(max_length=100,null=True,blank=True,unique=True)
	Year = models.PositiveSmallIntegerField()
	Runtime = models.CharField(max_length=10,null=True,blank=True)
	ImdbId = models.CharField(max_length=25,null=True,blank=True,unique=True)
	RottenTomatoesId = models.CharField(max_length=25,null=True,blank=True,unique=True)
	NetflixId = models.CharField(max_length=25,null=True,blank=True,unique=True)
	WikipediaId = models.CharField(max_length=100,null=True,blank=True,unique=True)
	CreatedAt= models.DateTimeField(auto_now_add=True)
	UpdatedAt = models.DateTimeField(auto_now=True)
	
	class Meta:
		unique_together = ('Title', 'Year')
	
	def clean(self):
		year = self.Year
		if year and year < 1901 and year > 2155:
			raise ValidationError("Year must be between 1901 and 2155 (inclusive).")
		urltitle = ''
		hasAlNum = False
		# Form UrlTitle and check basic requirements
		title = self.Title.encode('ascii', 'replace')
		if title and len(title) > 0:
			for char in title:
				if not hasAlNum and char.isalnum():
					hasAlNum = True
				if char.isalnum():
					urltitle += char.lower()
				# Replace unicode characters with ~
				elif char == '?':
					urltitle += '~'
				elif char.isspace():
					urltitle += '_'
		if hasAlNum and len(urltitle) > 0:
			self.UrlTitle = urltitle + '_' + str(year)
		else:
			raise ValidationError("Title must contain at least one alphanumeric character.")
		# Change WikipediaId to appropriate value with underscores instead of spaces
		wikiId = self.WikipediaId
		if wikiId:
			wikiId = wikiId.replace(' ', '_')
			if len(wikiId) > 0:
				self.WikipediaId = wikiId
			else:
				raise ValidationError("WikipediaId must contain at least one character.")
		
class Properties(models.Model):
	MovieId = models.ForeignKey(Movies,related_name='+')
	PropertyId = models.IntegerField()
	Type = models.PositiveSmallIntegerField()
	CreatedAt= models.DateTimeField(auto_now_add=True)
	UpdatedAt = models.DateTimeField(auto_now=True)
	
	def clean(self):
		type = self.Type
		if not (type and Type >= 0 and Type <= 3):
			raise ValidationError("Type must be between 0 and 3 (inclusive).")
	
	class Meta:
		unique_together = ('MovieId', 'PropertyId', 'Type')
	
class Associations(models.Model):
	ProfileId = models.ForeignKey(Profiles,related_name='+')
	MovieId = models.ForeignKey(Movies,related_name='+')
	Watched = models.BooleanField()
	Accessible = models.BooleanField()
	Source = models.CharField(max_length=45,null=True,blank=True)
	Rank = models.PositiveIntegerField(null=True,blank=True)
	Rating = models.PositiveSmallIntegerField(null=True,blank=True)
	Review = models.TextField(null=True,blank=True)
	CreatedAt= models.DateTimeField(null=True)
	UpdatedAt = models.DateTimeField(null=True)
	
	def clean(self):
		data = self.Rating
		if data and not (data >= 0 or data <= 100):
			raise ValidationError("Rating must be an integer between 1 and 100 (inclusive).")
	
	class Meta:
		unique_together = ('ProfileId', 'MovieId')
