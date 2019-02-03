import axios from 'axios';
import { globalState } from '../state';
import BaseModel from './base';
import moment from 'moment';

export default class Guild extends BaseModel {
  constructor(obj) {
    super();
    this.fromData(obj);
    this.config = null;
  }

  fromData(obj) {
    this.id = obj.id;
    this.ownerID = obj.owner_id;
    this.name = obj.name;
    this.icon = obj.icon;
    this.splash = obj.splash;
    this.region = obj.region;
    this.enabled = obj.enabled;
    this.whitelist = obj.whitelist;
    this.premium = obj.premium;
    this.role = obj.role;
    this.events.emit('update', this);
  }

  update() {
    return new Promise((resolve, reject) => {
      axios.get(`/api/guilds/${this.id}`).then((res) => {
        this.fromData(res.data);
        resolve(res.data);
      }).catch((err) => {
        reject(err.response.data);
      });
    });
  }

  getConfig(refresh = false) {
    if (this.config && !refresh) {
      return new Promise((resolve) => {
        resolve(this.config);
      });
    }

    return new Promise((resolve, reject) => {
      axios.get(`/api/guilds/${this.id}/config`).then((res) => {
        resolve(res.data);
      }).catch((err) => {
        reject();
      });
    });
  }


  getConfigHistory(id) {
    return new Promise((resolve, reject) => {
      axios.get(`/api/guilds/${id}/config/history`).then((res) => {
        let data = res.data
        data = data.map(obj => {
          obj.created_at = obj.created_at + '+00:00';
          obj.created_timestamp = +moment(obj.created_at);
          obj.created_diff = moment(obj.created_at).fromNow();
          obj.user.discriminator = String(obj.user.discriminator).padStart(4, "0");
          return obj;
        });
        resolve(data);
      }).catch((err) => {
        reject();
      });
    });
  }


  putConfig(config) {
    return new Promise((resolve, reject) => {
      axios.post(`/api/guilds/${this.id}/config`, {config: config}).then((res) => {
        resolve();
      }).catch((err) => {
        reject(err.response.data);
      });
    });
  }

  getInfractions(page, limit, sorted, filtered) {
    let params = {page, limit};

    if (sorted) {
      params.sorted = JSON.stringify(sorted)
    }

    if (filtered) {
      params.filtered = JSON.stringify(filtered)
    }

    return new Promise((resolve, reject) => {
      axios.get(`/api/guilds/${this.id}/infractions`, {params: params}).then((res) => {
        resolve(res.data);
      }).catch((err) => {
        reject(err.response.data);
      });
    });
  }

  givePremium() {
    return new Promise((resolve, reject) => {
      axios.post(`/api/guilds/${this.id}/premium`).then((res) => {
        this.update().then(() => {
          resolve()
        });
      }).catch((err) => {
        reject(err.response.data);
      });
    });
  }

  cancelPremium() {
    return new Promise((resolve, reject) => {
      axios.delete(`/api/guilds/${this.id}/premium`).then((res) => {
        this.update().then(() => {
          resolve()
        });
      }).catch((err) => {
        reject(err.response.data);
      });
    });
  }

  delete() {
    return new Promise((resolve, reject) => {
      axios.delete(`/api/guilds/${this.id}`).then((res) => {
        resolve();
      }).catch((err) => {
        reject(err.response.data);
      })
    });
  }
}
