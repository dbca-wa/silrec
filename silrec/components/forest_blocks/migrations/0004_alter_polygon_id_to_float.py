# Generated manually — column type unchanged in DB (blocked by view dependency)
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forest_blocks', '0003_alter_polygon_datetime_to_char'),
    ]

    state_operations = [
        migrations.AlterField(
            model_name='polygon',
            name='polygon_id',
            field=models.FloatField(primary_key=True, db_comment='Primary key', serialize=False),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations),
    ]
