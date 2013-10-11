"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import unittest
from django.test import TestCase
from django.db import models
from potatobase.testbase import PotatoTestCase

from .models import (
    GlobalOccuranceCount,
    Index,
    index_instance,
    unindex_instance,
    search
)

class SampleModel(models.Model):
    field1 = models.CharField(max_length=1024)
    field2 = models.CharField(max_length=1024)

class SearchTests(PotatoTestCase):
    def test_field_indexing(self):
        instance1 = SampleModel.objects.create(
            field1="bananas apples cherries plums oranges kiwi"
        )

        index_instance(instance1, ["field1"])

        self.assertEqual(1, Index.objects.filter(iexact="bananas").count())
        self.assertEqual(1, Index.objects.filter(iexact="bananas apples").count())
        self.assertEqual(1, Index.objects.filter(iexact="bananas apples cherries").count())
        self.assertEqual(1, Index.objects.filter(iexact="bananas apples cherries plums").count())

        #We only store up to 4 adjacent words
        self.assertEqual(0, Index.objects.filter(iexact="bananas apples cherries plums oranges").count())

        self.assertEqual(1, Index.objects.filter(iexact="apples").count())
        self.assertEqual(1, Index.objects.filter(iexact="apples cherries").count())
        self.assertEqual(1, Index.objects.filter(iexact="apples cherries plums").count())
        self.assertEqual(1, Index.objects.filter(iexact="apples cherries plums oranges").count())

        #We only store up to 4 adjacent words
        self.assertEqual(0, Index.objects.filter(iexact="apples cherries plums oranges kiwis").count())

    def test_ordering(self):
        instance1 = SampleModel.objects.create(field1="eat a fish")
        instance2 = SampleModel.objects.create(field1="eat a chicken")
        instance3 = SampleModel.objects.create(field1="sleep a lot")

        index_instance(instance1, ["field1"])
        index_instance(instance2, ["field1"])
        index_instance(instance3, ["field1"])

        results = search(SampleModel, "eat a")

        #Instance 3 should come last, because it only contains "a"
        self.assertEqual(instance3, results[2])

        results = search(SampleModel, "eat fish")

        self.assertEqual(instance1, results[0]) #Instance 1 matches 2 uncommon words
        self.assertEqual(instance2, results[1]) #Instance 2 matches 1 uncommon word

    def test_basic_searching(self):
        self.assertEqual(0, SampleModel.objects.count())
        self.assertEqual(0, GlobalOccuranceCount.objects.count())

        instance1 = SampleModel.objects.create(field1="Banana", field2="Apple")
        instance2 = SampleModel.objects.create(field1="banana", field2="Cherry")
        instance3 = SampleModel.objects.create(field1="BANANA")

        index_instance(instance1, ["field1", "field2"])
        self.assertEqual(2, Index.objects.count())
        self.assertEqual(1, GlobalOccuranceCount.objects.get(pk="banana").count)
        self.assertEqual(1, GlobalOccuranceCount.objects.get(pk="apple").count)

        index_instance(instance2, ["field1", "field2"])

        self.assertEqual(4, Index.objects.count())
        self.assertEqual(2, GlobalOccuranceCount.objects.get(pk="banana").count)
        self.assertEqual(1, GlobalOccuranceCount.objects.get(pk="apple").count)
        self.assertEqual(1, GlobalOccuranceCount.objects.get(pk="cherry").count)

        index_instance(instance3, ["field1"])
        self.assertEqual(5, Index.objects.count())
        self.assertEqual(3, GlobalOccuranceCount.objects.get(pk="banana").count)
        self.assertEqual(1, GlobalOccuranceCount.objects.get(pk="apple").count)
        self.assertEqual(1, GlobalOccuranceCount.objects.get(pk="cherry").count)

        self.assertItemsEqual([instance1, instance2, instance3], search(SampleModel, "banana"))
        self.assertItemsEqual([instance2], search(SampleModel, "cherry"))

        unindex_instance(instance1)

        self.assertItemsEqual([instance2, instance3], search(SampleModel, "banana"))
        self.assertItemsEqual([instance2], search(SampleModel, "cherry"))

    @unittest.skip("Not implemented yet")
    def test_logic_searching(self):
        instance1 = SampleModel.objects.create(field1="Banana", field2="Apple")
        instance2 = SampleModel.objects.create(field1="banana", field2="Cherry")
        instance3 = SampleModel.objects.create(field1="BANANA")

        index_instance(instance1, ["field1", "field2"])
        index_instance(instance2, ["field1", "field2"])
        index_instance(instance3, ["field1"])

        self.assertItemsEqual([instance1], search(SampleModel, "banana AND apple"))
        self.assertItemsEqual([instance1, instance2], search(SampleModel, "apple OR cherry"))

        unindex_instance(instance1)

        self.assertItemsEqual([], search(SampleModel, "banana AND apple"))
        self.assertItemsEqual([instance2], search(SampleModel, "apple OR cherry"))
