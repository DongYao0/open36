import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { styles } from "../styles";
import { navLinks } from "../constants";
import { logo, menu, close } from "../assets";

const Navbar = () => {
  const [active, setActive] = useState("");
  const [toggle, setToggle] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      if (scrollTop > 100) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener("scroll", handleScroll);

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // 登录态感知：读取 Vue 应用写入的 localStorage（同源 :8080 网关下共享）
  // open436_user / open436_guest_mode 由 Open436-Frontend 的 auth store 维护
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const checkAuth = () => {
      try {
        const u = JSON.parse(localStorage.getItem("open436_user") || "null");
        const guestMode = JSON.parse(
          localStorage.getItem("open436_guest_mode") || "false"
        );
        setUser(u);
        setIsLoggedIn(!!u || guestMode === true);
      } catch {
        setUser(null);
        setIsLoggedIn(false);
      }
    };
    checkAuth();
    // 登录在 Vue 完成后整页跳回本页会重新挂载；storage 事件兜底跨标签页同步
    window.addEventListener("storage", checkAuth);
    return () => window.removeEventListener("storage", checkAuth);
  }, []);

  // 头像：有真实头像用之，游客/无头像用昵称首字母占位
  const avatar =
    user?.avatar ||
    `https://ui-avatars.com/api/?name=${encodeURIComponent(
      user?.nickname || user?.username || "Guest"
    )}&background=915EFF&color=fff&size=64`;

  return (
    <nav
      className={`${
        styles.paddingX
      } w-full flex items-center py-5 fixed top-0 z-20 ${
        scrolled ? "bg-primary" : "bg-transparent"
      }`}
    >
      <div className='w-full flex justify-between items-center max-w-7xl mx-auto'>
        <Link
          to='/'
          className='flex items-center gap-2'
          onClick={() => {
            setActive("");
            window.scrollTo(0, 0);
          }}
        >
          <img src={logo} alt='logo' className='w-9 h-9 object-contain' />
          <p className='text-white-100 text-[18px] font-bold cursor-pointer flex '>
            OPEN&nbsp;
            <span className='sm:block hidden'> | 436 技术社区</span>
          </p>
        </Link>

        <ul className='list-none hidden sm:flex flex-row gap-10'>
          {navLinks.map((nav) => (
            <li
              key={nav.id}
              className='text-secondary hover:text-white-100 text-[18px] font-medium cursor-pointer transition-colors'
            >
              <a href={nav.href}>{nav.title}</a>
            </li>
          ))}
        </ul>

        {isLoggedIn ? (
          <a
            href='/app/mine'
            className='hidden sm:flex items-center gap-2 bg-white/10 hover:bg-white/20 border border-white/25 text-white-100 pl-1.5 pr-4 py-1.5 rounded-full text-[15px] font-medium transition-colors duration-200'
          >
            <img
              src={avatar}
              alt='我的'
              className='w-7 h-7 rounded-full object-cover ring-2 ring-white/30'
            />
            <span>我的</span>
          </a>
        ) : (
          <a
            href='/app/login'
            className='hidden sm:flex items-center border border-secondary hover:border-white-100 text-white-100 px-5 py-2 rounded-full text-[16px] font-medium transition-colors duration-200'
          >
            登录
          </a>
        )}

        <div className='sm:hidden flex flex-1 justify-end items-center'>
          <img
            src={toggle ? close : menu}
            alt='menu'
            className='w-[28px] h-[28px] object-contain'
            onClick={() => setToggle(!toggle)}
          />

          <div
            className={`${
              !toggle ? "hidden" : "flex"
            } p-6 black-gradient absolute top-20 right-0 mx-4 my-2 min-w-[140px] z-10 rounded-xl`}
          >
            <ul className='list-none flex justify-end items-start flex-1 flex-col gap-4'>
              {navLinks.map((nav) => (
                <li
                  key={nav.id}
                  className='font-poppins font-medium cursor-pointer text-[16px] text-secondary hover:text-white-100'
                  onClick={() => setToggle(false)}
                >
                  <a href={nav.href}>{nav.title}</a>
                </li>
              ))}
              <li className='font-poppins font-medium cursor-pointer text-[16px] mt-2'>
                {isLoggedIn ? (
                  <a
                    href='/app/mine'
                    onClick={() => setToggle(false)}
                    className='inline-flex items-center gap-2 bg-[#915EFF] text-white-100 px-4 py-2 rounded-full'
                  >
                    <img src={avatar} alt='我的' className='w-6 h-6 rounded-full object-cover' />
                    我的 →
                  </a>
                ) : (
                  <a
                    href='/app/login'
                    onClick={() => setToggle(false)}
                    className='inline-block border border-secondary text-white-100 px-4 py-2 rounded-full'
                  >
                    登录 →
                  </a>
                )}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
