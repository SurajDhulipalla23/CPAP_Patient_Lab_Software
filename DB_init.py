from pymodm import connect, MongoModel, fields
import ssl


def init_mongo_db():
    connect(
        "mongodb+srv://LucasR23:FinalProject" +
        "@bme547cluster.oppvfea.mongodb.net/" +
        "SleepLabRooms?retryWrites=true&w=majority",
        tlsAllowInvalidCertificates=True
    )


class SleepLabRooms(MongoModel):
    room_number = fields.IntegerField(primary_key=True)
    patient_name = fields.CharField()
    patient_mrn = fields.IntegerField()
    cpap_pressure = fields.IntegerField()
    cpap_calculations = cpap_calculations = fields.ListField(
        field=fields.ListField())


def add_new_room(room_number_arg, patient_name_arg, patient_mrn_arg,
                 cpap_pressure_arg, cpap_calculations_arg):
    room = SleepLabRooms(room_number=room_number_arg,
                         patient_name=patient_name_arg,
                         patient_mrn=patient_mrn_arg,
                         cpap_pressure=cpap_pressure_arg,
                         cpap_calculations=cpap_calculations_arg)
    room.save()
    print("Saved to database")


def get_users():
    for room in SleepLabRooms.objects.raw({}):
        print(SleepLabRooms.room_number)
        print(SleepLabRooms.patient_name)
    return


def populate_db():
    all = SleepLabRooms.objects.raw({})
    for x in all:
        x.delete()
    # Room 1
    all = SleepLabRooms.objects.raw({})
    for x in all:
        x.delete()

    add_new_room(1, "John Doe", 100, 15,
                 [["2023-11-29T10:00:00", 18, 2, "image1.png"],
                  ["2023-11-29T12:00:00", 17, 3, "image2.png"]])

    # Room 2
    add_new_room(2, "Jane Smith", 101, 10,
                 [["2023-11-29T11:00:00", 16, 1, "image3.png"],
                  ["2023-11-29T13:00:00", 15, 2, "image4.png"]])

    # Room 3
    add_new_room(3, "Alice Johnson", 102, 12,
                 [["2023-11-29T09:30:00", 19, 2, "image5.png"],
                  ["2023-11-29T11:30:00", 18, 4, "image6.png"]])

    # Room 4
    add_new_room(4, "Bob Brown", 103, 14,
                 [["2023-11-29T08:45:00", 20, 1, "image7.png"],
                  ["2023-11-29T10:45:00", 17, 3, "image8.png"]])


init_mongo_db()
populate_db()
get_users()

if __name__ == "__main__":
    patient = SleepLabRooms.objects.raw({"_id": 4}).first()
