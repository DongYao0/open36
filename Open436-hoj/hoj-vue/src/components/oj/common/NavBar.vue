<template>
  <div>
    <template v-if="!mobileNar">
      <div id="header">
        <el-menu
          :default-active="activeMenuName"
          mode="horizontal"
          router
          active-text-color="#2196f3"
          text-color="#495060"
        >
          <div class="logo">
            <el-tooltip
              :content="$t('m.Click_To_Change_Web_Language')"
              placement="bottom"
              effect="dark"
            >
              <el-image
                style="width: 139px; height: 50px"
                :src="imgUrl"
                fit="scale-down"
                @click="changeWebLanguage"
              ></el-image>
            </el-tooltip>
          </div>
          <template v-if="mode == 'defalut'">
            <el-menu-item index="/home"
              ><i class="el-icon-s-home"></i>{{ $t('m.NavBar_Home') }}</el-menu-item
            >
            <el-menu-item index="/problem"
              ><i class="el-icon-s-grid"></i
              >{{ $t('m.NavBar_Problem') }}</el-menu-item
            >
            <el-menu-item index="/training"
              ><i class="el-icon-s-claim"></i
              >{{ $t('m.NavBar_Training') }}</el-menu-item
            >
            <el-menu-item index="/contest"
              ><i class="el-icon-trophy"></i
              >{{ $t('m.NavBar_Contest') }}</el-menu-item
            >
            <el-menu-item index="/status"
              ><i class="el-icon-s-marketing"></i
              >{{ $t('m.NavBar_Status') }}</el-menu-item
            >
            <el-submenu index="rank">
              <template slot="title"
                ><i class="el-icon-s-data"></i>{{ $t('m.NavBar_Rank') }}</template
              >
              <el-menu-item index="/acm-rank">{{
                $t('m.NavBar_ACM_Rank')
              }}</el-menu-item>
              <el-menu-item index="/oi-rank">{{
                $t('m.NavBar_OI_Rank')
              }}</el-menu-item>
            </el-submenu>
            <el-menu-item index="/group"
              ><i
                class="fa fa-users navbar-icon"
              ></i
              >{{ $t('m.NavBar_Group') }}</el-menu-item
            >
        </template>
        <template v-else-if="mode == 'training'">
          <el-menu-item index="/home"
              ><i class="el-icon-s-home"></i>{{ $t('m.NavBar_Back_Home') }}</el-menu-item
            >
            <template v-if="$route.params.groupID">
              <el-menu-item :index="'/group/' + $route.params.groupID"
              ><i
                class="fa fa-users navbar-icon"
              ></i
              >{{ $t('m.NavBar_Group_Home') }}</el-menu-item>
            </template>
            <el-menu-item :index="getTrainingHomePath()"
              ><i class="el-icon-s-claim"></i>{{ $t('m.NavBar_Training_Home') }}</el-menu-item
            >
            <el-menu-item :index="getTrainingProblemListPath()"
              ><i class="fa fa-list navbar-icon"></i>{{ $t('m.Problem_List') }}</el-menu-item
            >
        </template>
        <template v-else-if="mode == 'contest'">
          <el-menu-item index="/home"
              ><i class="el-icon-s-home"></i>{{ $t('m.NavBar_Back_Home') }}</el-menu-item
            >
            <el-menu-item :index="'/contest/' + $route.params.contestID"
              ><i class="el-icon-trophy"></i>{{ $t('m.NavBar_Contest_Home') }}</el-menu-item
            >
            <el-menu-item :index="'/contest/' + $route.params.contestID + '/problems'"
              ><i class="fa fa-list navbar-icon"></i>{{ $t('m.Problem_List') }}</el-menu-item
            >
            <el-menu-item :index="'/contest/' + $route.params.contestID + '/submissions?onlyMine=true'"
              ><i class="el-icon-menu"></i>{{ $t('m.NavBar_Contest_Own_Submission') }}</el-menu-item
            >
            <el-menu-item :index="'/contest/' + $route.params.contestID + '/rank'"
              ><i class="fa fa-bar-chart navbar-icon"></i>{{ $t('m.NavBar_Contest_Rank') }}</el-menu-item
            >
        </template>
        <template v-else-if="mode == 'group'">
          <el-menu-item index="/home"
              ><i class="el-icon-s-home"></i>{{ $t('m.NavBar_Back_Home') }}</el-menu-item
            >
            <template v-if="$route.params.groupID">
              <el-menu-item :index="'/group/' + $route.params.groupID"
              ><i
                class="fa fa-users navbar-icon"
              ></i
              >{{ $t('m.NavBar_Group_Home') }}</el-menu-item>
            </template>
            <el-menu-item :index="'/group/' + $route.params.groupID + '/problem'"
              ><i class="fa fa-list navbar-icon"></i>{{ $t('m.Problem_List') }}</el-menu-item
            >
        </template>

          <div class="btn-menu">
            <el-button
              type="primary"
              size="medium"
              round
              @click="goToForum"
              icon="el-icon-s-promotion"
            >返回论坛
            </el-button>
          </div>
        </el-menu>
      </div>
      <div id="header-hidden" v-show="isScrolled">
      </div>
    </template>
    <template v-else>
      <div style="top:0px;left:0px;">
      <mu-appbar class="mobile-nav" color="primary">
        <mu-button icon slot="left" @click="opendrawer = !opendrawer">
          <i class="el-icon-s-unfold"></i>
        </mu-button>
        <el-tooltip
            :content="$t('m.Click_To_Change_Web_Language')"
            placement="bottom"
            effect="dark"
          >
          <span @click="changeWebLanguage">
          {{
            websiteConfig.shortName ? websiteConfig.shortName : 'OJ'
          }}
          </span>
        </el-tooltip>
        <mu-button
          flat
          slot="right"
          @click="goToForum"
        >返回论坛</mu-button>
      </mu-appbar>

      <mu-appbar style="width: 100%;">
        <!--占位，刚好占领导航栏的高度-->
      </mu-appbar>

      <mu-drawer :open.sync="opendrawer" :docked="false" :right="false">
        <mu-list toggle-nested>
          <mu-list-item
            button
            to="/home"
            @click="opendrawer = !opendrawer"
            active-class="mobile-menu-active"
          >
            <mu-list-item-action>
              <mu-icon value=":el-icon-s-home" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>{{ $t('m.NavBar_Home') }}</mu-list-item-title>
          </mu-list-item>

          <mu-list-item
            button
            to="/problem"
            @click="opendrawer = !opendrawer"
            active-class="mobile-menu-active"
          >
            <mu-list-item-action>
              <mu-icon value=":el-icon-s-grid" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>{{
              $t('m.NavBar_Problem')
            }}</mu-list-item-title>
          </mu-list-item>

          <mu-list-item
            button
            to="/training"
            @click="opendrawer = !opendrawer"
            active-class="mobile-menu-active"
          >
            <mu-list-item-action>
              <mu-icon value=":el-icon-s-claim" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>{{
              $t('m.NavBar_Training')
            }}</mu-list-item-title>
          </mu-list-item>

          <mu-list-item
            button
            to="/contest"
            @click="opendrawer = !opendrawer"
            active-class="mobile-menu-active"
          >
            <mu-list-item-action>
              <mu-icon value=":el-icon-trophy" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>{{
              $t('m.NavBar_Contest')
            }}</mu-list-item-title>
          </mu-list-item>

          <mu-list-item
            button
            to="/status"
            @click="opendrawer = !opendrawer"
            active-class="mobile-menu-active"
          >
            <mu-list-item-action>
              <mu-icon value=":el-icon-s-marketing" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>{{ $t('m.NavBar_Status') }}</mu-list-item-title>
          </mu-list-item>

          <mu-list-item
            button
            :ripple="false"
            nested
            :open="openSideMenu === 'rank'"
            @toggle-nested="openSideMenu = arguments[0] ? 'rank' : ''"
          >
            <mu-list-item-action>
              <mu-icon value=":el-icon-s-data" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>{{ $t('m.NavBar_Rank') }}</mu-list-item-title>
            <mu-list-item-action>
              <mu-icon
                class="toggle-icon"
                size="24"
                value=":el-icon-arrow-down"
              ></mu-icon>
            </mu-list-item-action>
            <mu-list-item
              button
              :ripple="false"
              slot="nested"
              to="/acm-rank"
              @click="opendrawer = !opendrawer"
              active-class="mobile-menu-active"
            >
              <mu-list-item-title>{{
                $t('m.NavBar_ACM_Rank')
              }}</mu-list-item-title>
            </mu-list-item>
            <mu-list-item
              button
              :ripple="false"
              slot="nested"
              to="/oi-rank"
              @click="opendrawer = !opendrawer"
              active-class="mobile-menu-active"
            >
              <mu-list-item-title>{{
                $t('m.NavBar_OI_Rank')
              }}</mu-list-item-title>
            </mu-list-item>
          </mu-list-item>

          <mu-list-item
            button
            to="/group"
            @click="opendrawer = !opendrawer"
            active-class="mobile-menu-active"
          >
            <mu-list-item-action>
              <mu-icon value=":fa fa-users" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>{{ $t('m.NavBar_Group') }}</mu-list-item-title>
          </mu-list-item>

          <mu-divider></mu-divider>

          <mu-list-item
            button
            @click="opendrawer = !opendrawer; goToForum()"
            active-class="mobile-menu-active"
          >
            <mu-list-item-action>
              <mu-icon value=":el-icon-s-promotion" size="24"></mu-icon>
            </mu-list-item-action>
            <mu-list-item-title>返回论坛</mu-list-item-title>
          </mu-list-item>
        </mu-list>
      </mu-drawer>
    </div>
    </template>
    
    <el-dialog
      :visible.sync="modalVisible"
      width="370px"
      class="dialog"
      :title="title"
      :close-on-click-modal="false"
    >
      <component :is="modalStatus.mode" v-if="modalVisible"></component>
      <div slot="footer" style="display: none"></div>
    </el-dialog>
  </div>
</template>
<script>
import Login from '@/components/oj/common/Login';
import Register from '@/components/oj/common/Register';
import ResetPwd from '@/components/oj/common/ResetPassword';
import MsgSvg from '@/components/oj/msg/msgSvg';
import { mapGetters, mapActions } from 'vuex';
import Avatar from 'vue-avatar';
import api from '@/common/api';
export default {
  components: {
    Login,
    Register,
    ResetPwd,
    Avatar,
    MsgSvg,
  },
  created(){
    this.page_width();
    window.onresize = () => {
      this.page_width();
      this.setHiddenHeaderHeight();
    };
  },
  mounted() {
    this.switchMode();
    this.setHiddenHeaderHeight();
    if (this.isAuthenticated) {
      this.getUnreadMsgCount();
      this.msgTimer = setInterval(() => {
        this.getUnreadMsgCount();
      }, 120 * 1000);
    }
  },
  beforeDestroy() {
    clearInterval(this.msgTimer);
  },
  data() {
    return {
      mode:'defalut',
      centerDialogVisible: false,
      mobileNar: false,
      opendrawer: false,
      openusermenu: false,
      openmsgmenu: false,
      openSideMenu: '',
      imgUrl: require('@/assets/logo.png'),
      avatarStyle:
        'display: inline-flex;width: 30px;height: 30px;border-radius: 50%;align-items: center;justify-content: center;text-align: center;user-select: none;',
    };
  },
  methods: {
    ...mapActions(['changeModalStatus']),
    page_width() {
      let screenWidth = window.screen.width;
      if (screenWidth < 992) {
        this.mobileNar = true;
      } else {
        this.mobileNar = false;
      }
    },
    handleBtnClick(mode) {
      this.changeModalStatus({
        mode,
        visible: true,
      });
    },
    handleRoute(route) {
      //电脑端导航栏路由跳转事件
      if (route && route.split('/')[1] != 'admin') {
        this.$router.push(route);
      } else {
        window.open('/admin/');
      }
    },
    goToForum() {
      window.location.href = '/';
    },
    handleCommand(route) {
      // 移动端导航栏路由跳转事件
      this.openusermenu = false;
      this.openmsgmenu = false;
      if (route && route.split('/')[1] != 'admin') {
        this.$router.push(route);
      } else {
        window.open('/admin/');
      }
    },
    getUnreadMsgCount() {
      api.getUnreadMsgCount().then((res) => {
        let data = res.data.data;
        this.$store.dispatch('updateUnreadMessageCount', data);
        let sumMsg =
          data.comment + data.reply + data.like + data.mine + data.sys;
        if (sumMsg > 0) {
          if (this.webLanguage == 'zh-CN') {
            this.$notify.info({
              title: '未读消息',
              message:
                '亲爱的【' +
                this.userInfo.username +
                '】，您有最新的' +
                sumMsg +
                '条未读消息，请注意查看！',
              position: 'bottom-right',
              duration: 5000,
            });
          } else {
            this.$notify.info({
              title: 'Unread Message',
              message:
                'Dear【' +
                this.userInfo.username +
                '】, you have the latest ' +
                sumMsg +
                ' unread messages. Please check them!',
              position: 'bottom-right',
              duration: 5000,
            });
          }
        }
      });
    },
    changeWebLanguage() {
      this.$store.commit('changeWebLanguage', { language: this.webLanguage == 'zh-CN' ? 'en-US' : 'zh-CN' });
    },
    setHiddenHeaderHeight(){
      if(!this.mobileNar){
        try {
          let headerHeight = document.getElementById('header').offsetHeight;
          document.getElementById('header-hidden').setAttribute('style','height:'+ headerHeight + 'px')
        } catch (e) {}
      }
    },
    switchMode(){
      if(this.$route.meta.fullScreenSource){
        this.mode = this.$route.meta.fullScreenSource;
      }else{
        this.mode = 'defalut';
      }
    },
    getTrainingHomePath(){
      let tid = this.$route.params.trainingID
      let gid = this.$route.params.groupID
      if(gid){
        return `/group/${gid}/training/${tid}`;
      }else{
        return `/training/${tid}`;
      }
    },
    getTrainingProblemListPath(){
      let tid = this.$route.params.trainingID
      let gid = this.$route.params.groupID
      if(gid){
        return `/group/${gid}/training/${tid}/problems`;
      }else{
        return `/training/${tid}/problems`;
      }
    }
  },
  computed: {
    ...mapGetters([
      'modalStatus',
      'userInfo',
      'isAuthenticated',
      'isAdminRole',
      'token',
      'websiteConfig',
      'unreadMessage',
      'webLanguage',
    ]),
    avatar() {
      return this.$store.getters.userInfo.avatar;
    },
    activeMenuName() {
      if (this.$route.path.split('/')[1] == 'submission-detail') {
        return '/status';
      } else if (this.$route.path.split('/')[1] == 'discussion-detail') {
        return '/discussion';
      }
      return '/' + this.$route.path.split('/')[1];
    },
    modalVisible: {
      get() {
        return this.modalStatus.visible;
      },
      set(value) {
        this.changeModalStatus({ visible: value });
      },
    },
    title: {
      get() {
        let ojName = this.websiteConfig.shortName
          ? this.websiteConfig.shortName
          : 'OJ';
        if (this.modalStatus.mode == 'ResetPwd') {
          return this.$i18n.t('m.Dialog_Reset_Password') + ' - ' + ojName;
        } else {
          return (
            this.$i18n.t('m.Dialog_' + this.modalStatus.mode) + ' - ' + ojName
          );
        }
      },
    },
  },
  watch: {
    isAuthenticated() {
      if (this.isAuthenticated) {
        if (this.msgTimer) {
          clearInterval(this.msgTimer);
        }
        this.getUnreadMsgCount();
        this.msgTimer = setInterval(() => {
          this.getUnreadMsgCount();
        }, 120 * 1000);
      } else {
        clearInterval(this.msgTimer);
      }
    },
    $route(){
      this.switchMode();
    }
  },
};
</script>
<style scoped>
#header {
  min-width: 300px;
  position: fixed;
  top: 0;
  left: 0;
  height: auto;
  width: 100%;
  z-index: 2000;
  background-color: #fff;
  box-shadow: 0 1px 5px 0 rgba(0, 0, 0, 0.1);
}
.mobile-nav {
  position: fixed;
  left: 0px;
  top: 0px;
  z-index: 2500;
  height: auto;
  width: 100%;
}

#drawer {
  position: fixed;
  left: 0px;
  bottom: 0px;
  z-index: 1000;
  width: 100%;
  box-shadow: 00px 0px 00px rgb(255, 255, 255), 0px 0px 10px rgb(255, 255, 255),
    0px 0px 0px rgb(255, 255, 255), 1px 1px 0px rgb(218, 218, 218);
}

.logo {
  cursor: pointer;
  margin-left: 2%;
  margin-right: 2%;
  float: left;
  width: 139px;
  height: 42px;
  margin-top: 5px;
}
.el-dropdown-link {
  cursor: pointer;
  color: #409eff !important;
}
.el-icon-arrow-down {
  font-size: 18px;
}
.drop-menu {
  float: right;
  margin-right: 30px;
  position: relative;
  font-weight: 500;
  right: 10px;
  margin-top: 18px;
  font-size: 18px;
}
.drop-avatar {
  float: right;
  margin-right: 15px;
  position: relative;
  margin-top: 16px;
}
.drop-msg {
  float: right;
  font-size: 25px;
  margin-right: 10px;
  position: relative;
  margin-top: 13px;
}
.drop-msg-count {
  margin-left: 2px;
}
.btn-menu {
  font-size: 16px;
  float: right;
  margin-right: 10px;
  margin-top: 12px;
}
/deep/ .el-dialog {
  border-radius: 10px !important;
  text-align: center;
}
/deep/ .el-dialog__header .el-dialog__title {
  font-size: 22px;
  font-weight: 600;
  font-family: Arial, Helvetica, sans-serif;
  line-height: 1em;
  color: #4e4e4e;
}
.el-submenu__title i {
  color: #495060 !important;
}
.el-menu-item {
  padding: 0 13px;
}
.el-menu-item:hover, .el-menu .el-menu-item:hover{
  border-bottom: 2px solid #2474b5 !important;
}
.el-menu .el-menu-item:hover, 
.el-menu .el-menu-item:hover i,
.el-submenu .el-submenu__title:hover,
.el-submenu .el-submenu__title:hover i{
  outline: 0 !important;
  color: #2E95FB !important;
  background: linear-gradient(270deg, #F2F7FC 0%, #FEFEFE 100%)!important;
  transition: all .2s ease;
}
.el-menu .el-menu-item.is-active, 
.el-menu .el-menu-item.is-active i,
.el-submenu.is-active,
.el-submenu.is-active i
{
  color: #2E95FB !important;
  background: linear-gradient(270deg, #F2F7FC 0%, #FEFEFE 100%)!important;
  transition: all .2s ease;
}
.el-menu--horizontal .el-menu .el-menu-item:hover, 
.el-submenu /deep/.el-submenu__title:hover {
  color: #2E95FB !important;
  background: linear-gradient(270deg, #F2F7FC 0%, #FEFEFE 100%)!important;
}
.el-menu-item i {
  color: #495060;
}
.is-active .el-submenu__title i,
.is-active {
  color: #2196f3 !important;
}
.el-menu-item.is-active i {
  color: #2196f3 !important;
}
.navbar-icon{
  margin-right: 5px !important;
  width: 24px !important;
  text-align: center !important;
}
</style>
