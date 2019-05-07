#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "zlib.h"
#include "deviceapps.pb-c.h"

#define MAGIC               0xFFFFFFFF
#define DEVICE_APPS_TYPE    1


typedef struct pbheader_s {
    uint32_t magic;
    uint16_t type;
    uint16_t length;
} pbheader;

#define PBHEADER        sizeof(struct pbheader_s)
#define PBHEADER_INIT   {MAGIC, 0, 0}


static int 
serialize_device(PyObject *dict, DeviceApps__Device *device) {
    char *keystr, *type, *id;
    PyObject *key, *value;
    Py_ssize_t pos = 0;

    while (PyDict_Next(dict, &pos, &key, &value)) {
        if (!PyString_Check(key)) {
            PyErr_SetString(PyExc_TypeError, "Device dict has non-string key");
            return -1;
        }
        keystr = PyString_AsString(key);
        if (strcmp(keystr, "id") == 0) {
            if (!PyString_Check(value)) {
                PyErr_SetString(PyExc_TypeError, "Device id expected type string");
                return -1;
            }
            id = PyString_AsString(value);
            device->has_id = 1;
            device->id.data = (uint8_t *)id;
            device->id.len = strlen(id);
        } else if (strcmp(keystr, "type") == 0) {
            if (!PyString_Check(value)) {
                PyErr_SetString(PyExc_TypeError, "Device type expected type string");
                return -1;
            }
            type = PyString_AsString(value);
            device->has_type = 1;
            device->type.data = (uint8_t *)type;
            device->type.len = strlen(type);
        }
    }
    return 0;
}


static int    
serialize_message(PyObject *dict, DeviceApps *msg) {
    int i, n;
    char *keystr;
    PyObject *key, *value, *app;
    Py_ssize_t pos = 0;

    if (!PyDict_Check(dict)) {
        PyErr_SetString(PyExc_TypeError, "Expected type dict");
        return -1;
    }

    while (PyDict_Next(dict, &pos, &key, &value)) {
        if (!PyString_Check(key)) {
            PyErr_SetString(PyExc_TypeError, "Dict has non-string key");
            return 1;
        }
        keystr = PyString_AsString(key);
        if (strcmp(keystr, "device") == 0) {
            if (!PyDict_Check(value)) {
                PyErr_SetString(PyExc_TypeError, "Expected type dict for key \"device\"");
                return -1;
            }
            if (serialize_device(value, msg->device)) {
                return -1;
            }
        } else if (strcmp(keystr, "lat") == 0) {
            if (PyFloat_Check(value)) {
                msg->lat = PyFloat_AsDouble(value);
            } else if (PyInt_Check(value)) {
                msg->lat = (double)PyInt_AsLong(value);
            } else {
                PyErr_SetString(PyExc_TypeError, "Expected type int or float for key \"lat\"");
                return -1;
            }
            msg->has_lat = -1;
        } else if (strcmp(keystr, "lon") == 0) {
            if (PyFloat_Check(value)) {
                msg->lon = PyFloat_AsDouble(value);
            } else if (PyInt_Check(value)) {
                msg->lon = (double)PyInt_AsLong(value);
            } else {
                PyErr_SetString(PyExc_TypeError, "Expected type int or float for key \"lon\"");
                return -1;
            }
            msg->has_lon = -1;
        } else if (strcmp(keystr, "apps") == 0) {
            n = PyList_Size(value);
            if (msg->n_apps < 0) {
                PyErr_SetString(PyExc_TypeError, "Expected type list for key \"apps\"");
                return -1;
            }
            msg->n_apps = n;
            msg->apps = malloc(sizeof(uint32_t) * n);
            for (i = 0; i < msg->n_apps; i++) {
                app = PyList_GetItem(value, i);
                if (!PyInt_Check(app)) {
                    PyErr_SetString(PyExc_TypeError, "App expected type int");
                    return -1;
                }
                msg->apps[i] = (uint32_t)PyInt_AsLong(app);
            }
        }
    }
    return 0;
}


static void 
free_msg_apps(DeviceApps *msg) {
    if (msg->apps != NULL)
        free(msg->apps);
}


int write_messages(PyObject *iter, gzFile gz) {
    void *buf;
    int len = 0, err = 0;
    PyObject *item;

    while ((item = PyIter_Next(iter)) != NULL) {
        DeviceApps msg = DEVICE_APPS__INIT;
        DeviceApps__Device device = DEVICE_APPS__DEVICE__INIT;
        msg.device = &device;

        err = serialize_message(item, &msg);
        Py_DECREF(item);

        if (err) {
            free_msg_apps(&msg);
            return -1;
        }

        Py_BEGIN_ALLOW_THREADS

        pbheader header = PBHEADER_INIT;
        header.type = DEVICE_APPS_TYPE;
        header.length = device_apps__get_packed_size(&msg);

        buf = malloc(header.length);
        device_apps__pack(&msg, buf);

        if ((gzwrite(gz, &header, PBHEADER) == PBHEADER) && (gzwrite(gz, buf, header.length) == header.length)) {
            len += PBHEADER;
            len += header.length;
        } else {
            err = 1;
        }

        free_msg_apps(&msg);
        free(buf);

        Py_END_ALLOW_THREADS

        if (err) {
            PyErr_SetString(PyExc_IOError, "Error writing to file");
            return -1;
        }
    }
    return len;
}


// Read iterator of Python dicts
// Pack them to DeviceApps protobuf and write to file with appropriate header
// Return number of written bytes as Python integer
static PyObject *
py_deviceapps_xwrite_pb(PyObject *self, PyObject *args) {
    int res;
    const char *path;
    gzFile gz;
    PyObject *o, *iter;

    if (!PyArg_ParseTuple(args, "Os", &o, &path))
        return NULL;
    
    if ((iter = PyObject_GetIter(o)) == NULL)
        return NULL;
    
    if ((gz = gzopen(path, "wb")) == NULL) {
        Py_DECREF(iter);
        PyErr_SetString(PyExc_IOError, "Can't open file");
        return NULL;
    }

    res = write_messages(iter, gz);
    Py_DECREF(iter);

    if (res == -1) {
        gzclose(gz);
        unlink(path);
        return NULL;
    }

    if (gzclose(gz) != Z_OK) {
        PyErr_SetString(PyExc_IOError, "Can't close file");
        return NULL;
    }

    return Py_BuildValue("i", res);
}

// Unpack only messages with type == DEVICE_APPS_TYPE
// Return iterator of Python dicts
static PyObject *
py_deviceapps_xread_pb(PyObject* self, PyObject* args) {
    const char* path;

    if (!PyArg_ParseTuple(args, "s", &path))
        return NULL;

    printf("Read from: %s\n", path);
    Py_RETURN_NONE;
}


static PyMethodDef PBMethods[] = {
     {"deviceapps_xwrite_pb", py_deviceapps_xwrite_pb, METH_VARARGS, "Write serialized protobuf to file fro iterator"},
     {"deviceapps_xread_pb", py_deviceapps_xread_pb, METH_VARARGS, "Deserialize protobuf from file, return iterator"},
     {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC initpb(void) {
     (void) Py_InitModule("pb", PBMethods);
}
